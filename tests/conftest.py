import os

# CRITICAL: ALWAYS override DATABASE_URL with TEST_DATABASE_URL for tests
# This ensures that when spo.extensions.db is initialized, it uses the test database
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest

from spo import create_app
from spo.extensions import db as _db


@pytest.fixture(scope="function")
def app():
    # DATABASE_URL should already point to test DB from module-level setup above
    app = create_app(start_jobs=False, run_seed=False)
    app.config.update(
        TESTING=True,
    )

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


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
