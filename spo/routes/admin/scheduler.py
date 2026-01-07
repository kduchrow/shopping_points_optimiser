"""Admin routes for managing scheduled jobs."""

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import ScheduledJob
from spo.services.scheduler import reload_scheduled_job


def register_admin_scheduler(app):
    """Register admin routes for scheduler management."""

    @app.route("/admin/scheduled_jobs", methods=["GET"])
    @login_required
    def admin_scheduled_jobs():
        """Show all scheduled jobs."""
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        jobs = ScheduledJob.query.order_by(ScheduledJob.job_name).all()
        return render_template("admin_scheduled_jobs.html", jobs=jobs)

    @app.route("/admin/scheduled_jobs/create", methods=["GET", "POST"])
    @login_required
    def admin_create_scheduled_job():
        """Create a new scheduled job."""
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            job_name = request.form.get("job_name")
            job_type = request.form.get("job_type")
            cron_expression = request.form.get("cron_expression")
            enabled = request.form.get("enabled") == "on"

            if not job_name or not job_type or not cron_expression:
                flash("Alle Pflichtfelder müssen ausgefüllt werden.", "error")
                return render_template("admin_scheduled_job_form.html", job=None)

            # Check if job_name already exists
            existing = ScheduledJob.query.filter_by(job_name=job_name).first()
            if existing:
                flash(f"Ein Job mit dem Namen '{job_name}' existiert bereits.", "error")
                return render_template("admin_scheduled_job_form.html", job=None)

            new_job = ScheduledJob(
                job_name=job_name,
                job_type=job_type,
                cron_expression=cron_expression,
                enabled=enabled,
                created_by_user_id=current_user.id,
            )
            db.session.add(new_job)
            db.session.commit()

            # Reload scheduler with new job
            reload_scheduled_job(new_job.id, app)

            flash(f"Job '{job_name}' wurde erstellt.", "success")
            return redirect(url_for("admin_scheduled_jobs"))

        return render_template("admin_scheduled_job_form.html", job=None)

    @app.route("/admin/scheduled_jobs/<int:job_id>/edit", methods=["GET", "POST"])
    @login_required
    def admin_edit_scheduled_job(job_id):
        """Edit an existing scheduled job."""
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        job = ScheduledJob.query.get_or_404(job_id)

        if request.method == "POST":
            job.job_name = request.form.get("job_name")
            job.job_type = request.form.get("job_type")
            job.cron_expression = request.form.get("cron_expression")
            job.enabled = request.form.get("enabled") == "on"

            db.session.commit()

            # Reload scheduler with updated job
            reload_scheduled_job(job.id, app)

            flash(f"Job '{job.job_name}' wurde aktualisiert.", "success")
            return redirect(url_for("admin_scheduled_jobs"))

        return render_template("admin_scheduled_job_form.html", job=job)

    @app.route("/admin/scheduled_jobs/<int:job_id>/toggle", methods=["POST"])
    @login_required
    def admin_toggle_scheduled_job(job_id):
        """Toggle enabled/disabled status of a scheduled job."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        job = ScheduledJob.query.get_or_404(job_id)
        job.enabled = not job.enabled
        db.session.commit()

        # Reload scheduler
        reload_scheduled_job(job.id, app)

        status = "aktiviert" if job.enabled else "deaktiviert"
        flash(f"Job '{job.job_name}' wurde {status}.", "success")

        if request.headers.get("Accept") == "application/json":
            return jsonify({"success": True, "enabled": job.enabled})

        return redirect(url_for("admin_scheduled_jobs"))

    @app.route("/admin/scheduled_jobs/<int:job_id>/delete", methods=["POST"])
    @login_required
    def admin_delete_scheduled_job(job_id):
        """Delete a scheduled job."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        job = ScheduledJob.query.get_or_404(job_id)
        job_name = job.job_name

        db.session.delete(job)
        db.session.commit()

        # Reload scheduler to remove job
        reload_scheduled_job(job_id, app)

        flash(f"Job '{job_name}' wurde gelöscht.", "success")
        return redirect(url_for("admin_scheduled_jobs"))

    return app
