import os

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# CRITICAL: ALWAYS override DATABASE_URL with TEST_DATABASE_URL for tests
# This ensures that when spo.extensions.db is initialized, it uses the test database
if "TEST_DATABASE_URL" in os.environ:
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

import pytest

from spo import create_app
from spo.extensions import db as _db


def ensure_test_database_exists():
    """Create test database if it doesn't exist."""
    # Parse TEST_DATABASE_URL to extract connection parameters
    test_db_url = os.environ.get("TEST_DATABASE_URL", "")
    if not test_db_url or "postgresql" not in test_db_url:
        # Not using PostgreSQL for tests, skip
        return

    # Extract connection params from URL like:
    # postgresql+psycopg2://user:password@host:port/dbname
    try:
        from urllib.parse import urlparse

        parsed = urlparse(test_db_url)
        host = parsed.hostname or "db"
        port = parsed.port or 5432
        user = parsed.username or "spo"
        password = parsed.password or "spo"
        dbname = parsed.path.lstrip("/") or "spo_test"

        # Connect to default 'postgres' database to create test database
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check if test database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (dbname,),
        )
        exists = cursor.fetchone()

        if not exists:
            print(f"Creating test database: {dbname}")
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            print(f"✅ Test database '{dbname}' created successfully")
        else:
            print(f"✅ Test database '{dbname}' already exists")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"⚠️  Warning: Could not ensure test database exists: {e}")
        print("Tests may fail if database doesn't exist")


# Ensure test database exists before any tests run
ensure_test_database_exists()


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


@pytest.fixture(scope="function")
def admin_user(app, db):
    """Create an admin user for tests using credentials from environment."""
    from spo.models import User

    with app.app_context():
        # Get test credentials from environment variables (required - no defaults)
        test_admin_username = os.environ.get("TEST_ADMIN_USERNAME")
        test_admin_password = os.environ.get("TEST_ADMIN_PASSWORD")

        if not test_admin_username or not test_admin_password:
            raise ValueError(
                "TEST_ADMIN_USERNAME and TEST_ADMIN_PASSWORD must be set in environment. "
                "Add them to your .env file."
            )

        admin = User()
        admin.username = test_admin_username
        admin.email = "admin@test.com"
        admin.role = "admin"
        admin.set_password(test_admin_password)
        db.session.add(admin)
        db.session.commit()

        # Store the plain password as an attribute for use in tests
        # (This is safe since it's only used in tests and the object is not persisted with this)
        admin._test_password = test_admin_password

        yield admin
