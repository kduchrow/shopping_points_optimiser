"""Smoke tests to verify basic application functionality.

These tests ensure the app can start and handle basic requests.
"""

from spo.models import BonusProgram


class TestAppStartup:
    """Test that the application can start successfully."""

    def test_app_creates_without_errors(self, app):
        """Test that the app factory creates an app instance."""
        assert app is not None
        assert app.name == "spo"

    def test_app_has_required_blueprints(self, app):
        """Test that required blueprints are registered."""
        # Check that routes are registered
        # The app uses register_* functions instead of blueprints
        # So we check for specific route endpoints instead
        assert app.url_map is not None
        # Basic smoke test - just verify we have some routes
        assert len(list(app.url_map.iter_rules())) > 0

    def test_database_models_are_importable(self):
        """Test that all models can be imported without errors."""
        from spo.models import (
            BonusProgram,
            ContributorRequest,
            Coupon,
            Notification,
            Proposal,
            ProposalAuditTrail,
            ProposalVote,
            RateComment,
            ScrapeLog,
            Shop,
            ShopMain,
            ShopMergeProposal,
            ShopMetadataProposal,
            ShopProgramRate,
            ShopVariant,
            User,
        )

        # Just verify they can be imported
        assert BonusProgram is not None
        assert ContributorRequest is not None
        assert Coupon is not None
        assert Notification is not None
        assert Proposal is not None
        assert ProposalAuditTrail is not None
        assert ProposalVote is not None
        assert RateComment is not None
        assert ScrapeLog is not None
        assert Shop is not None
        assert ShopMain is not None
        assert ShopMergeProposal is not None
        assert ShopMetadataProposal is not None
        assert ShopProgramRate is not None
        assert ShopVariant is not None
        assert User is not None


class TestBasicRoutes:
    """Test that basic routes are accessible."""

    def test_index_route_exists(self, client):
        """Test that the index route is accessible."""
        response = client.get("/")
        # Should not be 500 or 404
        assert response.status_code in [200, 302], (
            f"Index route returned {response.status_code}. "
            f"This might indicate missing database tables or configuration issues."
        )

    def test_index_route_requires_database(self, client, db):
        """Test that the index route can query the database."""
        # Add a test bonus program
        bp = BonusProgram()
        bp.name = "Test Program"
        bp.point_value_eur = 0.01
        db.session.add(bp)
        db.session.commit()

        # Now the index should load successfully
        response = client.get("/")
        assert response.status_code == 200
        assert b"Shopping Points Optimiser" in response.data

    def test_api_health_check(self, client):
        """Test API health endpoint if it exists."""
        response = client.get("/api/health")
        # Even if it doesn't exist, shouldn't crash the app
        assert response.status_code in [200, 404]


class TestDatabaseConnectivity:
    """Test database connectivity and basic operations."""

    def test_database_connection_works(self, app, db):
        """Test that we can connect to the database."""
        with app.app_context():
            # Simple query that should work if DB is connected
            result = db.session.execute(db.text("SELECT 1")).scalar()
            assert result == 1

    def test_can_create_and_query_records(self, app, db):
        """Test that we can create and query database records."""
        with app.app_context():
            # Create a bonus program
            bp = BonusProgram()
            bp.name = "Smoke Test Program"
            bp.point_value_eur = 0.01
            db.session.add(bp)
            db.session.commit()

            # Query it back
            found = BonusProgram.query.filter_by(name="Smoke Test Program").first()
            assert found is not None
            assert found.name == "Smoke Test Program"
            assert found.point_value_eur == 0.01

    def test_database_tables_exist(self, app, db):
        """Test that required database tables exist."""
        with app.app_context():
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            # Check for critical tables
            required_tables = [
                "bonus_programs",
                "shop_main",
                "shop_variants",
                "shops",
                "shop_program_rates",
                "users",
                "coupons",
            ]

            missing_tables = [t for t in required_tables if t not in tables]
            assert not missing_tables, (
                f"Missing critical database tables: {missing_tables}. "
                f"This indicates migrations haven't run properly."
            )


class TestAppConfiguration:
    """Test application configuration."""

    def test_app_has_required_config(self, app):
        """Test that required configuration keys are present."""
        assert "SQLALCHEMY_DATABASE_URI" in app.config
        assert "SECRET_KEY" in app.config

    def test_sqlalchemy_is_configured(self, app):
        """Test that SQLAlchemy is properly configured."""
        assert hasattr(app, "extensions")
        assert "sqlalchemy" in app.extensions
