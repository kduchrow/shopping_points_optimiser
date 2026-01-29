from flask import render_template


def register_legal(app):
    @app.route("/impressum", methods=["GET"])
    def impressum():
        return render_template("legal/impressum.html")

    @app.route("/datenschutz", methods=["GET"])
    def datenschutz():
        return render_template("legal/datenschutz.html")
