import os

import pytest

from spo import create_app
from spo.extensions import db as _db


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
            _db.drop_all()
            _db.create_all()
            yield app
            _db.session.remove()
            _db.drop_all()
    finally:
        # Restore original DATABASE_URL
        if original_db_url is not None:
            os.environ["DATABASE_URL"] = original_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]


@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    """Provide the database instance for tests."""
    with app.app_context():
        yield _db
