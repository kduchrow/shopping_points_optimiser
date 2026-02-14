"""Admin scraper jobs and status routes."""

import json
import uuid

from flask import flash, jsonify, render_template, request
from flask_login import current_user, login_required

from job_queue import job_queue
from spo.extensions import db
from spo.models import BonusProgram, ScrapeLog, Shop, ShopMain, ShopProgramRate, ShopVariant
from spo.services.dedup import run_deduplication
from spo.services.scrape_queue import (
    enqueue_coupon_import_job,
    enqueue_import_job,
    enqueue_scrape_job,
    get_rq_job_status,
)
from spo.services.scrape_queue_config import get_redis_connection
from spo.services.scrapers import (
    scrape_example,
    scrape_miles_and_more,
    scrape_payback,
    scrape_shoop,
    scrape_topcashback,
)


def register_admin_jobs(app):
    def _normalize_name(value: str) -> str:
        return " ".join(value.strip().lower().split())

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

    def _shop_suggestions(query: str | None, limit: int = 50) -> list[dict[str, str | int]]:
        if not query:
            return []
        from sqlalchemy import or_

        search = query.strip().lower()
        qs = ShopMain.query.filter_by(status="active")
        if search:
            qs = qs.outerjoin(ShopVariant, ShopMain.id == ShopVariant.shop_main_id).filter(
                or_(
                    ShopMain.canonical_name_lower.contains(search),
                    ShopVariant.source_name.ilike(f"%{query}%"),
                )
            )

        shop_mains = qs.distinct().order_by(ShopMain.canonical_name).limit(limit).all()
        results = []
        for shop_main in shop_mains:
            shop = Shop.query.filter_by(shop_main_id=shop_main.id).first()
            if not shop:
                continue
            results.append({"id": shop.id, "name": shop_main.canonical_name})
        return results

    def _shop_name_for_id(shop_id: int | None) -> str | None:
        if not shop_id:
            return None
        shop = Shop.query.filter_by(id=shop_id).first()
        if not shop or not shop.shop_main_id:
            return None
        main = ShopMain.query.filter_by(id=shop.shop_main_id).first()
        if not main:
            return None
        return main.canonical_name

    def _validate_coupon_import(payload: dict) -> dict:
        program = payload.get("program")
        coupons = payload.get("coupons")
        source = payload.get("source")

        missing_programs = []
        missing_shops = []

        program_names = set()
        has_coupon_programs = False
        if isinstance(program, str) and program.strip():
            program_names.add(program.strip())

        if isinstance(coupons, list):
            for c in coupons:
                if not isinstance(c, dict):
                    continue
                if c.get("program"):
                    has_coupon_programs = True
                    program_names.add(str(c.get("program")).strip())

                merchant = c.get("merchant") or c.get("shop") or c.get("shop_name") or c.get("name")
                shop_id = c.get("shop_id")
                if shop_id is None and merchant:
                    shop_id = _resolve_shop_id(str(merchant))
                if shop_id is None:
                    missing_shops.append(merchant or "<unknown>")

        program_optional = bool(source) and not has_coupon_programs

        for name in sorted({n for n in program_names if n}):
            if program_optional and name == (program or "").strip():
                continue
            exists = BonusProgram.query.filter(BonusProgram.name.ilike(name)).first()
            if not exists:
                missing_programs.append(name)

        return {
            "program": program,
            "coupon_count": len(coupons) if isinstance(coupons, list) else 0,
            "missing_programs": sorted(set(missing_programs)),
            "missing_shops": sorted(set(missing_shops)),
        }

    def _strip_optional_program(payload: dict) -> None:
        program = payload.get("program")
        source = payload.get("source")
        coupons = payload.get("coupons")
        if not (isinstance(program, str) and program.strip()) or not source:
            return
        has_coupon_programs = False
        if isinstance(coupons, list):
            for c in coupons:
                if isinstance(c, dict) and c.get("program"):
                    has_coupon_programs = True
                    break
        if has_coupon_programs:
            return
        payload["program"] = None

    @app.route("/admin/bonus_programs", methods=["GET"])
    @login_required
    def admin_bonus_programs():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        # Return only programs for which we have at least one active ShopProgramRate
        programs = (
            db.session.query(BonusProgram)
            .join(ShopProgramRate, BonusProgram.id == ShopProgramRate.program_id)
            .filter(ShopProgramRate.valid_to.is_(None))
            .group_by(BonusProgram.id)
            .order_by(BonusProgram.name.asc())
            .all()
        )
        return jsonify({"programs": [{"name": p.name} for p in programs]})

    def _run_scraper_job(scraper_func, success_message):
        job_id = job_queue.enqueue(scraper_func)
        if request.headers.get("Accept") == "application/json":
            return jsonify({"job_id": job_id, "status": "queued"})

        flash(success_message.format(job_id[:8]), "success")
        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        programs_data = [
            {"id": p.id, "name": p.name, "point_value_eur": p.point_value_eur} for p in programs
        ]
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs_data, logs=logs, job_id=job_id
        )

    @app.route("/admin/run_scraper", methods=["POST"])
    @login_required
    def admin_run_scraper():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        return _run_scraper_job(scrape_example, "Example-Scraper gestartet. Job ID: {}...")

    @app.route("/admin/run_payback", methods=["POST"])
    @login_required
    def admin_run_payback():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        return _run_scraper_job(scrape_payback, "Payback-Scraper gestartet. Job ID: {}...")

    @app.route("/admin/run_topcashback", methods=["POST"])
    @login_required
    def admin_run_topcashback():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        return _run_scraper_job(scrape_topcashback, "TopCashback-Scraper gestartet. Job ID: {}...")

    @app.route("/admin/run_miles_and_more", methods=["POST"])
    @login_required
    def admin_run_miles_and_more():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        return _run_scraper_job(
            scrape_miles_and_more, "Miles & More-Scraper gestartet. Job ID: {}..."
        )

    @app.route("/admin/run_shoop", methods=["POST"])
    @login_required
    def admin_run_shoop():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        return _run_scraper_job(scrape_shoop, "Shoop-Scraper gestartet. Job ID: {}...")

    @app.route("/admin/run_letyshops", methods=["POST"])
    @login_required
    def admin_run_letyshops():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        # Enqueue externally to the scraper worker so the run appears in worker logs
        job_id = enqueue_scrape_job("letyshops", requested_by=current_user.username)
        if request.headers.get("Accept") == "application/json":
            return jsonify({"job_id": job_id, "status": "queued"})

        flash(f"LetyShops-Scraper gestartet. Job ID: {job_id[:8]}...", "success")
        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        programs_data = [
            {"id": p.id, "name": p.name, "point_value_eur": p.point_value_eur} for p in programs
        ]
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs_data, logs=logs, job_id=job_id
        )

    @app.route("/admin/run_and_charge", methods=["POST"])
    @login_required
    def admin_run_and_charge():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403
        # Enqueue externally to the scraper worker so the run appears in worker logs
        job_id = enqueue_scrape_job("and_charge", requested_by=current_user.username)
        if request.headers.get("Accept") == "application/json":
            return jsonify({"job_id": job_id, "status": "queued"})

        flash(f"&Charge-Scraper gestartet. Job ID: {job_id[:8]}...", "success")
        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        programs_data = [
            {"id": p.id, "name": p.name, "point_value_eur": p.point_value_eur} for p in programs
        ]
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs_data, logs=logs, job_id=job_id
        )

    @app.route("/admin/run_deduplication", methods=["POST"])
    @login_required
    def admin_run_deduplication():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403

        # Get system user ID for attribution (use current admin user)
        job_id = job_queue.enqueue(run_deduplication, kwargs={"system_user_id": current_user.id})

        if request.headers.get("Accept") == "application/json":
            return jsonify({"job_id": job_id, "status": "queued"})

        flash(f"Shop-Deduplizierung gestartet. Job ID: {job_id[:8]}...", "success")
        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        programs_data = [
            {"id": p.id, "name": p.name, "point_value_eur": p.point_value_eur} for p in programs
        ]
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs_data, logs=logs, job_id=job_id
        )

    @app.route("/admin/import_consolidated/preview", methods=["POST"])
    @login_required
    def import_consolidated_preview():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        try:
            raw = file.read().decode("utf-8")
            payload = json.loads(raw)
        except Exception as exc:
            return jsonify({"error": f"Invalid JSON: {exc}"}), 400

        if not isinstance(payload, dict):
            return jsonify({"error": "Payload must be a JSON object"}), 400

        program = payload.get("program")
        shops = payload.get("shops")
        if not program or not isinstance(program, str):
            return jsonify({"error": "Missing or invalid program"}), 400
        if not isinstance(shops, list):
            return jsonify({"error": "shops must be an array"}), 400

        token = str(uuid.uuid4())
        redis_conn = get_redis_connection()
        redis_conn.setex(f"import:{token}", 3600, json.dumps(payload))

        return jsonify({"token": token, "program": program, "shop_count": len(shops)})

    @app.route("/admin/import_consolidated/confirm", methods=["POST"])
    @login_required
    def import_consolidated_confirm():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}
        token = data.get("token")
        if not token:
            return jsonify({"error": "Missing token"}), 400

        redis_conn = get_redis_connection()
        raw = redis_conn.get(f"import:{token}")
        if not raw:
            return jsonify({"error": "Token expired or not found"}), 404

        try:
            payload = json.loads(raw)
        except Exception:
            return jsonify({"error": "Stored payload is invalid"}), 500

        redis_conn.delete(f"import:{token}")
        job_id = enqueue_import_job(payload, requested_by=current_user.username)

        return jsonify({"job_id": job_id, "status": "queued"})

    @app.route("/admin/import_coupons/preview", methods=["POST"])
    @login_required
    def import_coupons_preview():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        try:
            raw = file.read().decode("utf-8")
            payload = json.loads(raw)
        except Exception as exc:
            return jsonify({"error": f"Invalid JSON: {exc}"}), 400

        if not isinstance(payload, dict):
            return jsonify({"error": "Payload must be a JSON object"}), 400

        if not isinstance(payload.get("coupons"), list):
            return jsonify({"error": "coupons must be an array"}), 400

        report = _validate_coupon_import(payload)
        rows = []
        for idx, coupon in enumerate(payload.get("coupons") or []):
            if not isinstance(coupon, dict):
                continue
            merchant = (
                coupon.get("merchant")
                or coupon.get("shop")
                or coupon.get("shop_name")
                or coupon.get("name")
                or ""
            )
            matched_shop_id = coupon.get("shop_id") or _resolve_shop_id(str(merchant))
            suggestions = _shop_suggestions(str(merchant), limit=50) if merchant else []
            matched_shop_name = None
            if matched_shop_id:
                matched_shop_name = next(
                    (s["name"] for s in suggestions if s["id"] == matched_shop_id), None
                )
                if not matched_shop_name:
                    matched_shop_name = _shop_name_for_id(matched_shop_id)

            rows.append(
                {
                    "index": idx,
                    "merchant": merchant,
                    "title": coupon.get("title") or coupon.get("name") or "",
                    "discount_text": coupon.get("discount_text") or "",
                    "value": coupon.get("value") or coupon.get("discount_value") or 0,
                    "url": coupon.get("url") or "",
                    "matched_shop_id": matched_shop_id,
                    "matched_shop_name": matched_shop_name,
                    "suggestions": suggestions,
                }
            )
        token = str(uuid.uuid4())
        redis_conn = get_redis_connection()
        redis_conn.setex(f"coupon-import:{token}", 3600, json.dumps(payload))

        return jsonify({"token": token, "rows": rows, **report})

    @app.route("/admin/import_coupons/confirm", methods=["POST"])
    @login_required
    def import_coupons_confirm():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}
        token = data.get("token")
        selections = data.get("selections")
        if not token:
            return jsonify({"error": "Missing token"}), 400
        if not isinstance(selections, list) or not selections:
            return jsonify({"error": "Missing selections"}), 400

        redis_conn = get_redis_connection()
        raw = redis_conn.get(f"coupon-import:{token}")
        if not raw:
            return jsonify({"error": "Token expired or not found"}), 404

        try:
            payload = json.loads(raw)
        except Exception:
            return jsonify({"error": "Stored payload is invalid"}), 500

        coupons = payload.get("coupons")
        if not isinstance(coupons, list):
            return jsonify({"error": "Stored payload is invalid"}), 500

        selected = []
        errors = []
        for selection in selections:
            if not isinstance(selection, dict):
                continue
            index = selection.get("index")
            try:
                index = int(index)
            except Exception:
                errors.append("Invalid coupon index")
                continue
            if index < 0 or index >= len(coupons):
                errors.append(f"Index out of range: {index}")
                continue

            shop_id = selection.get("shop_id")
            try:
                shop_id = int(shop_id)
            except Exception:
                errors.append(f"Missing shop for index {index}")
                continue

            coupon = dict(coupons[index])
            coupon["shop_id"] = shop_id
            merchant = selection.get("merchant")
            if merchant:
                coupon["merchant"] = str(merchant)
            selected.append(coupon)

        if errors:
            return jsonify({"error": "Invalid selections", "details": errors}), 400
        if not selected:
            return jsonify({"error": "No coupons selected"}), 400

        payload["coupons"] = selected

        report = _validate_coupon_import(payload)
        if report["missing_programs"] or report["missing_shops"]:
            return jsonify({"error": "Strict validation failed", **report}), 400

        redis_conn.delete(f"coupon-import:{token}")
        job_id = enqueue_coupon_import_job(payload, requested_by=current_user.username)

        return jsonify({"job_id": job_id, "status": "queued"})

    @app.route("/admin/job_status/<job_id>", methods=["GET"])
    @login_required
    def job_status(job_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        job = job_queue.get_job(job_id)
        # First check in-process (threaded) job queue
        if job:
            return jsonify(job.to_dict())

        # If not found, try RQ (external scraper-worker) jobs
        rq_info = get_rq_job_status(job_id)
        if rq_info:
            # Optionally include application-side ScrapeLog messages for the run_id
            include_logs = request.args.get("include_logs") == "1"
            if include_logs:
                run_id = rq_info.get("kwargs", {}).get("run_id")
                logs = []
                if run_id:
                    logs_q = (
                        ScrapeLog.query.filter(ScrapeLog.message.ilike(f"%run_id={run_id}%"))
                        .order_by(ScrapeLog.timestamp.desc())
                        .limit(50)
                        .all()
                    )
                    for log_entry in logs_q:
                        logs.append(
                            {
                                "timestamp": log_entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                "message": log_entry.message,
                            }
                        )
                rq_info["logs"] = logs

            return jsonify(rq_info)

        return jsonify({"error": "Job not found"}), 404

    @app.route("/admin/jobs", methods=["GET"])
    @login_required
    def list_jobs():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        all_jobs = job_queue.get_all_jobs()
        all_jobs.sort(key=lambda job: job.created_at, reverse=True)
        return jsonify([job.to_dict() for job in all_jobs[:20]])

    return app
