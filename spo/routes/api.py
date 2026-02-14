"""API endpoints for browser extension and scraper workers."""

import os
from datetime import datetime, timedelta

from flask import jsonify, request
from flask_login import current_user
from sqlalchemy import or_

from spo.extensions import db
from spo.models import BonusProgram, Coupon, ScrapeLog
from spo.models.proposals import Proposal
from spo.models.shops import Shop, ShopMain, ShopProgramRate, ShopVariant
from spo.models.user_preferences import UserFavoriteProgram
from spo.services.scrape_ingest import ingest_scrape_results
from spo.services.scrape_queue import enqueue_scrape_job


def register_api_routes(app):
    """Register API routes for the browser extension."""

    @app.after_request
    def after_request(response):
        """Add CORS headers for browser extension."""
        # Allow extension to access API
        origin = request.headers.get("Origin")
        if origin and origin.startswith("chrome-extension://"):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/api/shops", methods=["GET"])
    def api_get_shops():
        """Get all shops with their URLs for matching."""
        # Get all active ShopMain entries
        shop_mains = ShopMain.query.filter_by(status="active").all()

        shops_data = []
        for shop_main in shop_mains:
            # Get at least one Shop entry for each ShopMain
            shop = Shop.query.filter_by(shop_main_id=shop_main.id).first()
            if not shop:
                continue

            shop_data = {
                "id": shop.id,
                "name": shop_main.canonical_name,
                "url": shop_main.website or "",
                "alternative_urls": [],
            }

            # Add alternative URLs from approved URL proposals
            proposals_query = Proposal.query.filter_by(shop_id=shop.id, proposal_type="url")
            if current_user.is_authenticated:
                proposals = proposals_query.filter(
                    or_(Proposal.status == "approved", Proposal.user_id == current_user.id)
                ).all()
            else:
                proposals = proposals_query.filter_by(status="approved").all()

            for proposal in proposals:
                if proposal.source_url and proposal.source_url not in shop_data["alternative_urls"]:
                    shop_data["alternative_urls"].append(proposal.source_url)

            shops_data.append(shop_data)

        return jsonify({"shops": shops_data})

    @app.route("/api/shops/<int:shop_id>/rates", methods=["GET"])
    def api_get_shop_rates(shop_id):
        """Get all rates for a specific shop."""
        from spo.models.core import BonusProgram

        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role not in ["moderator", "admin"]:
            return jsonify({"error": "Forbidden"}), 403

        shop = Shop.query.get_or_404(shop_id)
        shop_main = ShopMain.query.get(shop.shop_main_id) if shop.shop_main_id else None

        # Get all sibling shops for this ShopMain to ensure all rates are included
        shop_ids = (
            [s.id for s in Shop.query.filter_by(shop_main_id=shop.shop_main_id).all()]
            if shop.shop_main_id
            else [shop.id]
        )
        rates = ShopProgramRate.query.filter(
            ShopProgramRate.shop_id.in_(shop_ids), ShopProgramRate.valid_to.is_(None)
        ).all()

        # Group by program and calculate effective values
        program_map = {}
        for rate in rates:
            program = db.session.get(BonusProgram, rate.program_id)
            if not program:
                continue

            # Calculate effective value (same as evaluate route)
            points_per_eur = float(rate.points_per_eur or 0)
            cashback_pct = float(rate.cashback_pct or 0)
            point_value_eur = float(program.point_value_eur or 0.005)

            # Effective value per EUR: points_value + cashback
            effective_value = (points_per_eur * point_value_eur) + (cashback_pct / 100.0)

            rate_data = {
                "id": rate.id,
                "points_per_eur": points_per_eur,
                "cashback_pct": cashback_pct,
                "point_value_eur": point_value_eur,
                "rate_type": rate.rate_type or "shop",
                "effective_value": round(effective_value, 4),
            }

            # Add incentive text if available
            if hasattr(rate, "rate_note") and rate.rate_note:
                rate_data["incentive_text"] = rate.rate_note

            if program.name not in program_map:
                program_map[program.name] = {
                    "program": program.name,
                    "program_id": program.id,
                    "point_value_eur": point_value_eur,
                    "best_value": effective_value,
                    "rates": [],
                }
            else:
                # Update best value if this rate is better
                if effective_value > program_map[program.name]["best_value"]:
                    program_map[program.name]["best_value"] = effective_value

            program_map[program.name]["rates"].append(rate_data)

        # Sort programs by best_value (descending)
        programs_list = sorted(program_map.values(), key=lambda p: p["best_value"], reverse=True)

        return jsonify(
            {
                "shop": {
                    "id": shop.id,
                    "name": shop_main.canonical_name if shop_main else shop.name,
                    "url": shop_main.website if shop_main else "",
                },
                "programs": programs_list,
            }
        )

    @app.route("/api/user/status", methods=["GET"])
    def api_user_status():
        """Check if user is logged in."""
        favorite_ids = []
        if current_user.is_authenticated:
            favorite_ids = [
                fav.program_id
                for fav in UserFavoriteProgram.query.filter_by(user_id=current_user.id).all()
            ]

        return jsonify(
            {
                "logged_in": current_user.is_authenticated,
                "username": current_user.username if current_user.is_authenticated else None,
                "is_admin": (
                    current_user.role == "admin" if current_user.is_authenticated else False
                ),
                "is_moderator": (
                    current_user.role == "moderator" if current_user.is_authenticated else False
                ),
                "favorite_program_ids": favorite_ids,
                "has_favorites": bool(favorite_ids),
            }
        )

    @app.route("/api/proposals/url", methods=["POST"])
    def api_create_url_proposal():
        """Create a URL proposal for a shop."""
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json()
        shop_id = data.get("shop_id")
        url = data.get("url")

        if not shop_id or not url:
            return jsonify({"error": "shop_id and url are required"}), 400

        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"error": "Shop not found"}), 404

        # Check if proposal already exists
        existing = Proposal.query.filter_by(
            shop_id=shop_id, proposal_type="url", source_url=url
        ).first()

        if existing:
            return jsonify(
                {
                    "message": "Proposal already exists",
                    "proposal_id": existing.id,
                    "status": existing.status,
                }
            )

        # Create new URL proposal
        proposal = Proposal(
            proposal_type="url",
            shop_id=shop_id,
            source_url=url,
            user_id=current_user.id,
            status="pending",  # Follow standard approval flow
            approved_by_system=False,
            source="browser_extension",
        )

        db.session.add(proposal)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Proposal created successfully",
                    "proposal_id": proposal.id,
                    "status": proposal.status,
                }
            ),
            201,
        )

    def _scraper_token_valid() -> bool:
        expected = os.environ.get("SCRAPER_API_TOKEN")
        if not expected:
            return False
        provided = request.headers.get("X-Scraper-Token")
        return provided == expected

    def _normalize_name(value: str) -> str:
        return " ".join(value.strip().lower().split())

    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(value), fmt)
            except Exception:
                continue
        return None

    def _resolve_shop_id(merchant: str) -> int | None:
        if not merchant:
            return None
        norm = _normalize_name(merchant)

        main = ShopMain.query.filter(ShopMain.canonical_name_lower == norm).first()
        if main:
            shop = Shop.query.filter_by(shop_main_id=main.id).first()
            if shop:
                return shop.id

        variant = ShopVariant.query.filter(ShopVariant.source_name.ilike(merchant)).first()
        if variant:
            shop = Shop.query.filter_by(shop_main_id=variant.shop_main_id).first()
            if shop:
                return shop.id

        shop = Shop.query.filter(Shop.name.ilike(merchant)).first()
        if shop:
            return shop.id

        return None

    @app.route("/api/scrape-jobs", methods=["POST"])
    def api_enqueue_scrape_job():
        if not _scraper_token_valid():
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        program = data.get("program")
        if not program:
            return jsonify({"error": "program is required"}), 400

        job_id = enqueue_scrape_job(program, requested_by="api")
        return jsonify({"job_id": job_id})

    @app.route("/api/scrape-results", methods=["POST"])
    def api_ingest_scrape_results():
        if not _scraper_token_valid():
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        program = data.get("program")
        shops = data.get("shops")
        run_id = data.get("run_id")

        if not program or shops is None:
            return jsonify({"error": "program and shops are required"}), 400
        if not isinstance(shops, list):
            return jsonify({"error": "shops must be a list"}), 400

        ingested = ingest_scrape_results(shops, source=program)
        db.session.add(
            ScrapeLog(message=f"Scraper ingest: {program} ({ingested} shops, run_id={run_id})")
        )
        db.session.commit()

        return jsonify({"ingested": ingested, "run_id": run_id, "program": program})

    @app.route("/api/coupon-import", methods=["POST"])
    def api_import_coupons():
        if not _scraper_token_valid():
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        program_name = data.get("program")
        coupons = data.get("coupons")
        run_id = data.get("run_id")

        if coupons is None:
            return jsonify({"error": "coupons are required"}), 400
        if not isinstance(coupons, list):
            return jsonify({"error": "coupons must be a list"}), 400

        program = None
        if isinstance(program_name, str) and program_name.strip():
            program = BonusProgram.query.filter(BonusProgram.name.ilike(program_name)).first()
            if not program:
                return jsonify({"error": f"Program not found: {program_name}"}), 400

        missing_shops = []
        resolved = []

        for c in coupons:
            if not isinstance(c, dict):
                continue
            merchant = c.get("merchant") or c.get("shop") or c.get("shop_name") or c.get("name")
            shop_id = c.get("shop_id")
            if shop_id is None and merchant:
                shop_id = _resolve_shop_id(str(merchant))

            if shop_id is None:
                missing_shops.append(merchant or "<unknown>")
                continue

            resolved.append((c, shop_id))

        if missing_shops:
            return (
                jsonify({"error": "Missing shops", "missing_shops": sorted(set(missing_shops))}),
                400,
            )

        ingested = 0
        for c, shop_id in resolved:
            coupon_type = c.get("coupon_type") or "discount"
            name = c.get("title") or c.get("name") or "Coupon"
            description = c.get("note") or c.get("description") or c.get("discount_text") or ""
            value = c.get("value") or c.get("discount_value") or 0
            try:
                value = float(value)
            except Exception:
                value = 0.0
            combinable = c.get("combinable")

            valid_from = _parse_date(c.get("valid_from"))
            valid_to = _parse_date(c.get("valid_to"))
            if not valid_from:
                valid_from = datetime.utcnow()
            if not valid_to:
                valid_to = valid_from + timedelta(days=30)

            existing_query = Coupon.query.filter(
                Coupon.shop_id == shop_id,
                Coupon.name == name,
                Coupon.status == "active",
            )
            if program:
                existing_query = existing_query.filter(Coupon.program_id == program.id)
            else:
                existing_query = existing_query.filter(Coupon.program_id.is_(None))

            existing = existing_query.all()
            now = datetime.utcnow()
            for prev in existing:
                prev.status = "inactive"
                prev.valid_to = now

            coupon = Coupon(
                coupon_type=coupon_type,
                name=name,
                description=description,
                shop_id=shop_id,
                program_id=program.id if program else None,
                value=value,
                combinable=combinable,
                valid_from=valid_from,
                valid_to=valid_to,
                source_url=c.get("url"),
            )
            db.session.add(coupon)
            ingested += 1

        program_label = program_name or "<none>"
        db.session.add(
            ScrapeLog(
                message=f"Coupon import: {program_label} ({ingested} coupons, run_id={run_id})"
            )
        )
        db.session.commit()

        return jsonify({"ingested": ingested, "run_id": run_id, "program": program_name})
