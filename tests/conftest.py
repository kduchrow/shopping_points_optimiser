import os
import subprocess
import sys

import pytest

from spo import create_app
from spo.extensions import db as _db
from spo.models import (
    BonusProgram,
    RateComment,
    Shop,
    ShopMain,
    ShopMergeProposal,
    ShopProgramRate,
    ShopVariant,
    User,
)
from spo.services.dedup import get_or_create_shop_main


# --- LOGGED IN ADMIN FIXTURE FOR ADMIN ROUTE TESTS ---
@pytest.fixture(scope="function")
def logged_in_admin(client, admin_user):
    """
    Logs in the admin user and returns the test client with an authenticated session.
    """
    response = client.post(
        "/login",
        data={"username": admin_user.username, "password": admin_user._test_password},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return client


print("[DEBUG] conftest.py loaded and executing in test environment.")


# --- FUNCTION-SCOPED DB CLEANUP FIXTURE ---
@pytest.fixture(autouse=True, scope="function")
def clean_db_per_test(app):
    """
    Drop and recreate all tables before each test to ensure a clean DB state.
    """
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        _db.session.commit()


# --- SESSION-SCOPED DB CLEANUP AND MIGRATION FIXTURE ---
@pytest.fixture(scope="session", autouse=True)
def clean_and_migrate_test_db():
    """
    Drop all tables, recreate schema, and apply Alembic migrations before any tests run.
    Ensures a clean test DB for every test session.
    """
    app = create_app(run_seed=False)
    with app.app_context():
        print("[DEBUG] Dropping all tables in test DB...")
        _db.drop_all()
        _db.session.commit()
        print("[DEBUG] Creating all tables in test DB...")
        _db.create_all()
        _db.session.commit()
        print("[DEBUG] Applying Alembic migrations...")
        # Run Alembic upgrade head using subprocess to ensure migrations are applied
        # Find project root (where alembic.ini is located)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alembic_ini = os.path.join(project_root, "alembic.ini")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "-c", alembic_ini, "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        print("[DEBUG] Alembic output:", result.stdout)
        if result.returncode != 0:
            print("[ERROR] Alembic migration failed:", result.stderr)
            raise RuntimeError("Alembic migration failed")
        print("[DEBUG] Test DB is clean and migrated.")


@pytest.fixture(scope="session")
def app():
    app = create_app(run_seed=False)
    return app


# Utility fixture to create a test shop and program for protected and evaluation tests
@pytest.fixture(scope="function")
def test_resources(app, db):
    print("DEBUG: ShopMain:", ShopMain, ShopMain.__module__)
    print("DEBUG: Shop:", Shop, Shop.__module__)
    print("DEBUG: BonusProgram:", BonusProgram, BonusProgram.__module__)
    import uuid

    with app.app_context():
        unique_id = str(uuid.uuid4())[:8]
        # Create ShopMain
        shop_main = ShopMain(
            canonical_name=f"Test Shop Main {unique_id}",
            canonical_name_lower=f"test shop main {unique_id}",
            website=f"https://testshop{unique_id}.com",
            status="active",
        )
        # assign id separately to avoid passing unsupported __init__ parameter
        shop_main.id = str(uuid.uuid4())
        print("ShopMain:", type(shop_main), repr(shop_main))
        db.session.add(shop_main)
        db.session.commit()

        # Create Shop
        shop = Shop(name=f"Test Shop {unique_id}", shop_main_id=shop_main.id)
        print("Shop:", type(shop), repr(shop))
        db.session.add(shop)
        db.session.commit()

        # Create BonusProgram
        from datetime import datetime

        program = BonusProgram(name=f"Test Program {unique_id}", point_value_eur=0.01)
        program.created_at = datetime.utcnow()
        print("BonusProgram:", type(program), repr(program))
        db.session.add(program)
        db.session.commit()

        # Create ShopProgramRate
        rate = ShopProgramRate(
            shop_id=shop.id, program_id=program.id, points_per_eur=1.0, cashback_pct=0.0
        )
        db.session.add(rate)
        db.session.commit()

        # Create a test admin user (for RateComment, ShopMergeProposal, etc.)
        admin_user = User.query.filter_by(username="test_admin").first()
        if not admin_user:
            admin_user = User(username="test_admin", email="admin@test.com", role="admin")
            admin_user.set_password("test_password")
            db.session.add(admin_user)
            db.session.commit()

        # Create ShopVariant for merge proposals
        variant_a = ShopVariant(
            shop_main_id=shop_main.id, source="test_source_a", source_name="Test Variant A"
        )
        db.session.add(variant_a)
        db.session.commit()
        variant_b = ShopVariant(
            shop_main_id=shop_main.id, source="test_source_b", source_name="Test Variant B"
        )
        db.session.add(variant_b)
        db.session.commit()

        # Create ShopMergeProposal
        merge_proposal = ShopMergeProposal(
            variant_a_id=variant_a.id,
            variant_b_id=variant_b.id,
            proposed_by_user_id=admin_user.id,
            reason="Test merge",
            status="PENDING",
        )
        db.session.add(merge_proposal)
        db.session.commit()

        # Create RateComment
        rate_comment = RateComment(
            rate_id=rate.id,
            reviewer_id=admin_user.id,
            comment_type="FEEDBACK",
            comment_text="Test comment",
        )
        db.session.add(rate_comment)
        db.session.commit()

        # Create metadata proposal dummy (if your model exists, add here)
        # ...

        yield {
            "shop": shop,
            "program": program,
            "rate": rate,
            "merge_proposal": merge_proposal,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "rate_comment": rate_comment,
            "admin_user": admin_user,
        }


@pytest.fixture(scope="function")
def session(app):
    with app.app_context():
        yield _db.session


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def admin_user(app, db):
    """Create an admin user for tests using credentials from environment."""
    with app.app_context():
        # Get test credentials from environment variables (required - no defaults)
        test_admin_username = os.environ.get("TEST_ADMIN_USERNAME")
        test_admin_password = os.environ.get("TEST_ADMIN_PASSWORD")

        if not test_admin_username or not test_admin_password:
            raise ValueError(
                "TEST_ADMIN_USERNAME and TEST_ADMIN_PASSWORD must be set in environment. "
                "Add them to your .env file."
            )

        admin = User.query.filter_by(username=test_admin_username).first()
        if not admin:
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


# --- SHOP TEST DATA FIXTURE (für Dropdown- und API-Tests) ---
@pytest.fixture(scope="function")
def shop_test_data(app, session):
    """Create test shops and bonus program for dropdown and API tests."""
    # Create test bonus program
    program = BonusProgram(name="Test Program", point_value_eur=0.01)
    session.add(program)
    session.flush()

    # Create test shops with various names for search testing
    test_shop_names = [
        "Amazon",
        "amazon.de",
        "REWE",
        "Edeka",
        "Lidl",
        "Aldi",
        "MediaMarkt",
        "Saturn",
        "Zalando",
        "Otto",
    ]

    for name in test_shop_names:
        # Create ShopMain entry using dedup service
        shop_main, _, _ = get_or_create_shop_main(
            shop_name=name, source="test", source_id=f"test_{name}"
        )

        # Create Shop entry linked to ShopMain
        shop = Shop(name=name, shop_main_id=shop_main.id)
        session.add(shop)
        session.flush()

        # Add rate for the shop
        rate = ShopProgramRate(
            shop_id=shop.id, program_id=program.id, points_per_eur=2.0, cashback_pct=1.5
        )
        session.add(rate)

    session.commit()
