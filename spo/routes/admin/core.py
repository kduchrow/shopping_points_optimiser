"""Core admin dashboard routes."""

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import BonusProgram, ScrapeLog


def register_admin_core(app):
    @app.route("/admin", methods=["GET"])
    @login_required
    def admin():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Seite.", "error")
            return redirect(url_for("index"))
        from spo.models.core import User
        from spo.models.logs import ScheduledJob

        users = User.query.order_by(User.created_at.desc()).all()
        jobs = ScheduledJob.query.order_by(ScheduledJob.job_name).all()
        programs = BonusProgram.query.order_by(BonusProgram.name).all()
        programs_data = [
            {"id": p.id, "name": p.name, "point_value_eur": p.point_value_eur} for p in programs
        ]
        return render_template(
            "admin.html", users=users, scheduled_jobs=jobs, programs=programs_data
        )

    @app.route("/admin/add_program", methods=["POST"])
    @login_required
    def admin_add_program():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        name = request.form.get("name", "").strip()
        try:
            point_value_eur = float(request.form.get("point_value_eur", 0.01))
        except ValueError:
            point_value_eur = 0.01

        if name:
            existing = BonusProgram.query.filter_by(name=name).first()
            if not existing:
                new_program = BonusProgram(name=name, point_value_eur=point_value_eur)
                db.session.add(new_program)
                db.session.commit()
                db.session.add(
                    ScrapeLog(message=f"Program added: {name} (€{point_value_eur} per point)")
                )
                db.session.commit()

        return redirect("/admin")

    @app.route("/admin/program/<int:program_id>", methods=["POST"])
    @login_required
    def admin_update_program(program_id):
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        program = BonusProgram.query.get(program_id)
        if not program:
            flash("Programm nicht gefunden.", "error")
            return redirect("/admin")

        old_name = program.name
        name = request.form.get("name", "").strip()
        try:
            point_value_eur = float(request.form.get("point_value_eur", program.point_value_eur))
        except ValueError:
            flash("Ungültige Punkwertigkeit.", "error")
            return redirect("/admin")

        if name and name != old_name:
            # Check if name already exists
            existing = BonusProgram.query.filter_by(name=name).first()
            if existing:
                flash("Programmname existiert bereits.", "error")
                return redirect("/admin")
            program.name = name

        program.point_value_eur = point_value_eur
        db.session.commit()
        db.session.add(
            ScrapeLog(
                message=f"Program updated: {old_name} → {program.name} (€{point_value_eur} per point)"
            )
        )
        db.session.commit()
        flash(f"Programm '{program.name}' aktualisiert.", "success")

        return redirect("/admin")

    @app.route("/admin/program/<int:program_id>/delete", methods=["POST"])
    @login_required
    def admin_delete_program(program_id):
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        program = BonusProgram.query.get(program_id)
        if not program:
            flash("Programm nicht gefunden.", "error")
            return redirect("/admin")

        program_name = program.name
        db.session.delete(program)
        db.session.commit()
        db.session.add(ScrapeLog(message=f"Program deleted: {program_name}"))
        db.session.commit()
        flash(f"Programm '{program_name}' gelöscht.", "success")

        return redirect("/admin")

    return app
