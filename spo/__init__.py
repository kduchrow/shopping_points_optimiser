import os
from flask import Flask

from spo.extensions import db, login_manager


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, '..', 'templates'),
        static_folder=os.path.join(base_dir, '..', 'static'),
    )

    # Import heavy modules lazily to avoid circular imports when scrapers use spo.* helpers
    from job_queue import job_queue
    from spo.routes.auth import register_auth
    from spo.routes.public import register_public
    from spo.routes.proposals import register_proposals
    from spo.routes.admin import register_admin
    from spo.routes.notifications import register_notifications
    from spo.models import User

    default_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'instance', 'shopping_points.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.abspath(default_db_path)}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        seed_initial_data()

    register_auth(app)
    register_public(app)
    register_proposals(app)
    register_admin(app)
    register_notifications(app)

    job_queue.set_app(app)
    job_queue.start()

    return app


def seed_initial_data():
    from spo.models import BonusProgram, User
    from spo.services import bonus_programs as bp_service
    from spo.services import seed as seed_service

    bonus_count = BonusProgram.query.count()
    if bonus_count == 0:
        bp_service.register_defaults()
        seed_service.register_example_shop()

    admin_password = os.environ.get('ADMIN_PASSWORD')
    if admin_password:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@localhost', role='admin')
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
