import os

from flask import Flask

from spo.extensions import db, login_manager
from spo.version import __version__

DEFAULT_GITHUB_URL = "https://github.com/kduchrow/shopping_points_optimiser"
DEFAULT_DB_URL = "postgresql+psycopg2://spo:spo@localhost:5432/spo"


def create_app(*, start_jobs: bool = True, run_seed: bool = True):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "..", "templates"),
        static_folder=os.path.join(base_dir, "..", "static"),
    )

    # Import heavy modules lazily to avoid circular imports when scrapers use spo.* helpers
    from job_queue import job_queue
    from spo.models import User
    from spo.routes.admin import register_admin
    from spo.routes.admin.scheduler import register_admin_scheduler
    from spo.routes.auth import register_auth
    from spo.routes.notifications import register_notifications
    from spo.routes.proposals import register_proposals
    from spo.routes.public import register_public

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["DEBUG"] = os.environ.get("DEBUG", "False").lower() == "true"
    app.config["APP_VERSION"] = __version__
    app.config["GITHUB_REPO_URL"] = os.environ.get("GITHUB_REPO_URL", DEFAULT_GITHUB_URL)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Clean up stale job runs on startup
    with app.app_context():
        try:
            from spo.models import ScheduledJobRun

            stale_runs = ScheduledJobRun.query.filter(
                ScheduledJobRun.status.in_(["running", "queued"])
            ).all()
            if stale_runs:
                for run in stale_runs:
                    run.status = "failed"
                    run.message = "Container restarted while job was running"
                db.session.commit()
        except Exception:
            # Table might not exist yet on first startup
            pass

    @app.context_processor
    def inject_meta():
        return {
            "app_version": app.config.get("APP_VERSION", __version__),
            "github_repo_url": app.config.get("GITHUB_REPO_URL", DEFAULT_GITHUB_URL),
        }

    if run_seed:
        with app.app_context():
            seed_initial_data()

    register_auth(app)
    register_public(app)
    register_proposals(app)
    register_admin(app)
    register_admin_scheduler(app)
    register_notifications(app)

    # Register job types (always, even if scheduler isn't started)
    from spo.services.dedup import run_deduplication
    from spo.services.scheduler import init_scheduler, register_job_type
    from spo.services.scrapers import (
        scrape_example,
        scrape_miles_and_more,
        scrape_payback,
        scrape_topcashback,
    )

    register_job_type("deduplication", run_deduplication)
    register_job_type("scrape_payback", scrape_payback)
    register_job_type("scrape_miles_and_more", scrape_miles_and_more)
    register_job_type("scrape_topcashback", scrape_topcashback)
    register_job_type("scrape_example", scrape_example)

    if start_jobs and os.environ.get("DISABLE_JOB_QUEUE", "false").lower() != "true":
        job_queue.set_app(app)
        job_queue.start()
        init_scheduler(app)

    return app


def seed_initial_data():
    from sqlalchemy import inspect

    from spo.models import BonusProgram, User
    from spo.services import bonus_programs as bp_service
    from spo.services import seed as seed_service

    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        return

    bonus_count = BonusProgram.query.count()
    if bonus_count == 0:
        bp_service.register_defaults()
        seed_service.register_example_shop()

    admin_password = os.environ.get("ADMIN_PASSWORD")
    if admin_password:
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(username="admin", email="admin@localhost", role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
