from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user, current_user

from spo.extensions import db
from spo.models import ContributorRequest, Proposal, User


def register_auth(app):
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')

            if not username or not email or not password:
                flash('Alle Felder sind erforderlich.', 'error')
                return redirect(url_for('register'))

            if User.query.filter_by(username=username).first():
                flash('Benutzername bereits vorhanden.', 'error')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email bereits registriert.', 'error')
                return redirect(url_for('register'))

            user = User(username=username, email=email, role='viewer')
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash('Registrierung erfolgreich! Bitte melden Sie sich an.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                if user.status == 'banned':
                    flash('Ihr Konto wurde gesperrt.', 'error')
                    return redirect(url_for('login'))
                login_user(user)
                flash(f'Willkommen, {user.username}!', 'success')
                return redirect(url_for('index'))

            flash('Ungültiger Benutzername oder Passwort.', 'error')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Sie wurden abgemeldet.', 'success')
        return redirect(url_for('index'))

    @app.route('/profile')
    @login_required
    def profile():
        contributor_request = ContributorRequest.query.filter_by(user_id=current_user.id).first()
        proposals = Proposal.query.filter_by(user_id=current_user.id).all()
        return render_template('profile.html', contributor_request=contributor_request, proposals=proposals)

    @app.route('/request-contributor', methods=['POST'])
    @login_required
    def request_contributor():
        if current_user.role == 'contributor':
            flash('Sie sind bereits Contributor.', 'info')
            return redirect(url_for('profile'))

        existing = ContributorRequest.query.filter_by(user_id=current_user.id, status='pending').first()
        if existing:
            flash('Sie haben bereits eine ausstehende Anfrage.', 'info')
            return redirect(url_for('profile'))

        request_obj = ContributorRequest(user_id=current_user.id)
        db.session.add(request_obj)
        db.session.commit()

        flash('Contributor-Anfrage eingereicht. Warten Sie auf Admin-Bestätigung.', 'success')
        return redirect(url_for('profile'))

    return app
