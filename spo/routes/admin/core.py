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
        return render_template("admin.html")

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

    return app
