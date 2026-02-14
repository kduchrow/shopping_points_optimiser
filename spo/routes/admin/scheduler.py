"""Admin routes for managing scheduled jobs."""

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import ScheduledJob, ScheduledJobRun
from spo.services.scheduler import (
    JOB_REGISTRY,
    cancel_job_run,
    reload_scheduled_job,
    trigger_job_now,
)


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
        if request.args.get("json") == "1":
            # Return jobs as JSON for AJAX loading
            def serialize(job):
                return {
                    "id": job.id,
                    "job_name": job.job_name,
                    "job_type": job.job_type,
                    "cron_expression": job.cron_expression,
                    "enabled": job.enabled,
                    "last_run_at": (
                        job.last_run_at.strftime("%Y-%m-%d %H:%M:%S") if job.last_run_at else None
                    ),
                    "last_run_status": job.last_run_status,
                    "last_run_message": job.last_run_message,
                }

            return jsonify({"jobs": [serialize(j) for j in jobs]})
        # For non-JSON requests, redirect to the main admin dashboard (tab is loaded dynamically)
        return redirect(url_for("admin"))

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
                available_job_types = list(JOB_REGISTRY.keys())
                return render_template(
                    "admin_scheduled_job_form.html",
                    job=None,
                    available_job_types=available_job_types,
                )

            # Check if job_name already exists
            existing = ScheduledJob.query.filter_by(job_name=job_name).first()
            if existing:
                flash(f"Ein Job mit dem Namen '{job_name}' existiert bereits.", "error")
                available_job_types = list(JOB_REGISTRY.keys())
                return render_template(
                    "admin_scheduled_job_form.html",
                    job=None,
                    available_job_types=available_job_types,
                )

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
            return redirect(url_for("admin"))

        available_job_types = list(JOB_REGISTRY.keys())
        return render_template(
            "admin_scheduled_job_form.html", job=None, available_job_types=available_job_types
        )

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

        available_job_types = list(JOB_REGISTRY.keys())
        return render_template(
            "admin_scheduled_job_form.html", job=job, available_job_types=available_job_types
        )

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

        # Prevent deleting a scheduled job that currently has active runs
        active_runs = (
            ScheduledJobRun.query.filter_by(scheduled_job_id=job.id)
            .filter(ScheduledJobRun.status.in_(["running", "queued"]))
            .count()
        )
        if active_runs:
            msg = f"Job '{job_name}' has {active_runs} active run(s) and cannot be deleted while running."
            if request.headers.get("Accept") == "application/json":
                return jsonify({"success": False, "message": msg}), 400
            flash(msg, "error")
            return redirect(url_for("admin_scheduled_jobs"))

        # delete run logs first to satisfy FK constraint
        ScheduledJobRun.query.filter_by(scheduled_job_id=job.id).delete()
        db.session.delete(job)
        db.session.commit()

        # Reload scheduler to remove job
        reload_scheduled_job(job_id, app)

        flash(f"Job '{job_name}' wurde gelöscht.", "success")

        # If the client expects JSON (AJAX), return a JSON success response
        if request.headers.get("Accept") == "application/json":
            return jsonify({"success": True, "message": f"Job '{job_name}' wurde gelöscht."})

        return redirect(url_for("admin_scheduled_jobs"))

    @app.route("/admin/scheduled_jobs/<int:job_id>/run", methods=["POST"])
    @login_required
    def admin_run_scheduled_job(job_id):
        """Manually trigger a scheduled job immediately."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        ok, msg = trigger_job_now(job_id, ignore_enabled=True, app=app)
        if ok:
            flash(f"Job wurde gestartet: {msg}", "success")
        else:
            flash(f"Job konnte nicht gestartet werden: {msg}", "error")

        if request.headers.get("Accept") == "application/json":
            return jsonify({"success": ok, "message": msg})
        return redirect(url_for("admin_scheduled_jobs"))

    @app.route("/admin/scheduled_jobs/<int:job_id>/logs", methods=["GET"])
    @login_required
    def admin_scheduled_job_logs(job_id):
        """Show run logs for a specific scheduled job."""
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        job = ScheduledJob.query.get_or_404(job_id)
        limit = request.args.get("limit", 50, type=int)
        limit = min(limit, 500)  # Max 500 runs
        runs = (
            ScheduledJobRun.query.filter_by(scheduled_job_id=job.id)
            .order_by(ScheduledJobRun.created_at.desc())
            .limit(limit)
            .all()
        )
        if request.args.get("json") == "1" or request.headers.get("Accept") == "application/json":
            return jsonify(
                {
                    "logs": [
                        {
                            "timestamp": (
                                run.created_at.strftime("%Y-%m-%d %H:%M:%S")
                                if run.created_at
                                else ""
                            ),
                            "message": run.message or "",
                        }
                        for run in runs
                    ]
                }
            )
        return render_template("admin_scheduled_job_logs.html", job=job, runs=runs)

    @app.route("/admin/scheduled_jobs/runs/<int:run_id>/cancel", methods=["POST"])
    @login_required
    def admin_cancel_job_run(run_id):
        """Cancel a running job execution."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        run = ScheduledJobRun.query.get_or_404(run_id)
        if run.status not in ("queued", "running"):
            return jsonify({"error": f"Cannot cancel job with status {run.status}"}), 400

        # Request cancellation
        was_running = cancel_job_run(run_id)
        if was_running:
            flash("Job wurde zum Abbruch markiert.", "success")
        else:
            flash("Job läuft nicht oder konnte nicht abgebrochen werden.", "warning")

        if request.headers.get("Accept") == "application/json":
            return jsonify({"success": was_running})
        return redirect(url_for("admin_scheduled_job_logs", job_id=run.scheduled_job_id))

    return app
