"""Admin scraper jobs and status routes."""

from flask import flash, jsonify, render_template, request
from flask_login import current_user, login_required

from job_queue import job_queue
from spo.models import BonusProgram, ScrapeLog, Shop
from spo.services.dedup import run_deduplication
from spo.services.scrapers import (
    scrape_example,
    scrape_miles_and_more,
    scrape_payback,
    scrape_shoop,
    scrape_topcashback,
)


def register_admin_jobs(app):
    @app.route("/admin/bonus_programs", methods=["GET"])
    @login_required
    def admin_bonus_programs():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403
        programs = BonusProgram.query.order_by(BonusProgram.name.asc()).all()
        return jsonify({"programs": [{"name": p.name} for p in programs]})

    def _run_scraper_job(scraper_func, success_message):
        job_id = job_queue.enqueue(scraper_func)
        if request.headers.get("Accept") == "application/json":
            return jsonify({"job_id": job_id, "status": "queued"})

        flash(success_message.format(job_id[:8]), "success")
        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs, logs=logs, job_id=job_id
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
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs, logs=logs, job_id=job_id
        )

    @app.route("/admin/job_status/<job_id>", methods=["GET"])
    @login_required
    def job_status(job_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        job = job_queue.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify(job.to_dict())

    @app.route("/admin/jobs", methods=["GET"])
    @login_required
    def list_jobs():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        all_jobs = job_queue.get_all_jobs()
        all_jobs.sort(key=lambda job: job.created_at, reverse=True)
        return jsonify([job.to_dict() for job in all_jobs[:20]])

    return app
