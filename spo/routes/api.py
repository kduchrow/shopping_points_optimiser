"""API endpoints for browser extension."""

from flask import jsonify, request
from flask_login import current_user
from sqlalchemy import or_

from spo.extensions import db
from spo.models.proposals import Proposal
from spo.models.shops import Shop, ShopMain, ShopProgramRate
from spo.models.user_preferences import UserFavoriteProgram


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
