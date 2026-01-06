import os

import pytest

from spo import create_app
from spo.extensions import db


@pytest.fixture(scope="function")
def app():
    # Set DATABASE_URL environment variable before create_app is called
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")

    try:
        app = create_app(start_jobs=False, run_seed=False)
        app.config.update(
            TESTING=True,
        )

        with app.app_context():
            db.drop_all()
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        yield db.session


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()
