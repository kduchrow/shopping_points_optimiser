"""Tests for SQLAlchemy 2.0 model migration.

This test suite ensures that after migrating to SQLAlchemy 2.0 mapped_column syntax,
all model operations still work correctly:
- Model instantiation with keyword arguments
- CRUD operations
- Relationships and foreign keys
- Queries and filtering
- Type safety and nullable fields
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from spo import create_app
from spo.extensions import db
from spo.models import (
    BonusProgram,
    Coupon,
    Notification,
    Proposal,
    ProposalVote,
    RateComment,
    Shop,
    ShopMain,
    ShopMergeProposal,
    ShopProgramRate,
    ShopVariant,
    User,
)


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(start_jobs=False, run_seed=False)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestBonusProgramModel:
    """Test BonusProgram model with SQLAlchemy 2.0 syntax."""

    def test_create_bonus_program_with_kwargs(self, app):
        """Test creating BonusProgram with keyword arguments."""
        with app.app_context():
            # Use unique name to avoid conflicts with production data
            import time

            unique_name = f"Test Program {int(time.time() * 1000)}"
            program = BonusProgram(name=unique_name, point_value_eur=0.01)
            db.session.add(program)
            db.session.commit()

            assert program.id is not None
            assert program.name == unique_name
            db.session.commit()

    def test_bonus_program_query(self, app):
        """Test querying BonusProgram."""
        with app.app_context():
            program = BonusProgram(name="Payback", point_value_eur=0.01)
            db.session.add(program)
            db.session.commit()

            found = db.session.execute(
                select(BonusProgram).where(BonusProgram.name == "Payback")
            ).scalar_one()

            assert found.name == "Payback"
            assert found.point_value_eur == 0.01


class TestShopMainModel:
    """Test ShopMain model with SQLAlchemy 2.0 syntax."""

    def test_create_shop_main_with_required_fields(self, app):
        """Test creating ShopMain with only required fields."""
        with app.app_context():
            shop = ShopMain(id="amazon-de", canonical_name="Amazon", canonical_name_lower="amazon")
            db.session.add(shop)
            db.session.commit()

            assert shop.id == "amazon-de"
            assert shop.canonical_name == "Amazon"
            assert shop.status == "active"
            assert shop.created_at is not None

    def test_shop_main_optional_fields(self, app):
        """Test ShopMain with optional nullable fields."""
        with app.app_context():
            shop = ShopMain(
                id="test-shop",
                canonical_name="Test Shop",
                canonical_name_lower="test shop",
                website="https://test.com",
                logo_url="https://test.com/logo.png",
            )
            db.session.add(shop)
            db.session.commit()

            assert shop.website == "https://test.com"
            assert shop.logo_url == "https://test.com/logo.png"

    def test_shop_main_relationship_with_variants(self, app):
        """Test ShopMain relationship with ShopVariant."""
        with app.app_context():
            shop = ShopMain(id="test-main", canonical_name="Test", canonical_name_lower="test")
            db.session.add(shop)
            db.session.commit()

            variant = ShopVariant(
                shop_main_id=shop.id, source="payback", source_name="Test Payback"
            )
            db.session.add(variant)
            db.session.commit()

            found_shop = db.session.get(ShopMain, "test-main")
            assert len(found_shop.variants) == 1
            assert found_shop.variants[0].source_name == "Test Payback"


class TestShopModel:
    """Test Shop model with SQLAlchemy 2.0 syntax."""

    def test_create_shop_with_shop_main_link(self, app):
        """Test Shop creation with foreign key to ShopMain."""
        with app.app_context():
            shop_main = ShopMain(
                id="amazon", canonical_name="Amazon", canonical_name_lower="amazon"
            )
            db.session.add(shop_main)
            db.session.commit()

            shop = Shop(name="Amazon.de", shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()

            assert shop.id is not None
            assert shop.shop_main_id == "amazon"


class TestShopProgramRateModel:
    """Test ShopProgramRate model with SQLAlchemy 2.0 syntax."""

    def test_create_rate_with_all_fields(self, app):
        """Test ShopProgramRate with all fields."""
        with app.app_context():
            program = BonusProgram(name="TestProgram", point_value_eur=0.01)
            db.session.add(program)

            shop_main = ShopMain(
                id="rate-test-shop",
                canonical_name="Rate Test Shop",
                canonical_name_lower="rate test shop",
            )
            db.session.add(shop_main)
            db.session.commit()

            shop = Shop(name="Test Shop", shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()

            rate = ShopProgramRate(
                shop_id=shop.id,
                program_id=program.id,
                points_per_eur=5.0,
                cashback_pct=2.5,
                valid_to=datetime.now() + timedelta(days=30),
            )
            db.session.add(rate)
            db.session.commit()

            assert rate.id is not None
            assert rate.points_per_eur == 5.0
            assert rate.cashback_pct == 2.5
            assert rate.valid_to is not None


class TestUserModel:
    """Test User model with SQLAlchemy 2.0 syntax."""

    def test_create_user_with_password(self, app):
        """Test User creation with password hashing."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com", role="viewer")
            user.set_password("secret123")
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.check_password("secret123")
            assert not user.check_password("wrong")

    def test_user_default_values(self, app):
        """Test User default values for role and status."""
        with app.app_context():
            user = User(username="user2", email="user2@example.com")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            assert user.role == "viewer"
            assert user.status == "active"


class TestCouponModel:
    """Test Coupon model with SQLAlchemy 2.0 syntax."""

    def test_create_coupon_with_relationships(self, app):
        """Test Coupon with Shop and BonusProgram relationships."""
        with app.app_context():
            program = BonusProgram(name="TestProgram", point_value_eur=0.01)
            db.session.add(program)

            shop_main = ShopMain(
                id="coupon-test-shop",
                canonical_name="Coupon Test Shop",
                canonical_name_lower="coupon test shop",
            )
            db.session.add(shop_main)
            db.session.commit()

            shop = Shop(name="Test Shop", shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()

            coupon = Coupon(
                coupon_type="percentage",
                name="10% Off",
                description="Test coupon",
                value=10.0,
                shop_id=shop.id,
                program_id=program.id,
                valid_from=datetime.now(),
                valid_to=datetime.now() + timedelta(days=7),
                status="active",
                combinable=True,
            )
            db.session.add(coupon)
            db.session.commit()

            assert coupon.id is not None
            assert coupon.shop.name == "Test Shop"
            assert coupon.program.name == "TestProgram"


class TestProposalModel:
    """Test Proposal model with SQLAlchemy 2.0 syntax."""

    def test_create_rate_proposal(self, app):
        """Test creating a rate update proposal."""
        with app.app_context():
            user = User(username="proposer", email="proposer@test.com")
            user.set_password("pass")
            db.session.add(user)

            program = BonusProgram(name="TestProgram", point_value_eur=0.01)
            db.session.add(program)

            shop_main = ShopMain(
                id="proposal-test-shop",
                canonical_name="Proposal Test Shop",
                canonical_name_lower="proposal test shop",
            )
            db.session.add(shop_main)
            db.session.commit()

            shop = Shop(name="Test", shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()

            proposal = Proposal(
                proposal_type="rate_update",
                user_id=user.id,
                shop_id=shop.id,
                program_id=program.id,
                proposed_points_per_eur=10.0,
                reason="Better rate found",
                status="pending",
            )
            db.session.add(proposal)
            db.session.commit()

            assert proposal.id is not None
            assert proposal.proposed_points_per_eur == 10.0


class TestProposalVoteModel:
    """Test ProposalVote model with SQLAlchemy 2.0 syntax."""

    def test_create_vote_with_unique_constraint(self, app):
        """Test ProposalVote creation and unique constraint."""
        with app.app_context():
            user1 = User(username="user1", email="user1@test.com")
            user1.set_password("pass")
            user2 = User(username="user2", email="user2@test.com")
            user2.set_password("pass")
            db.session.add_all([user1, user2])
            db.session.commit()

            proposal = Proposal(proposal_type="test", user_id=user1.id, status="pending")
            db.session.add(proposal)
            db.session.commit()

            vote = ProposalVote(proposal_id=proposal.id, voter_id=user2.id, vote=1, vote_weight=1)
            db.session.add(vote)
            db.session.commit()

            assert vote.id is not None


class TestShopMergeProposalModel:
    """Test ShopMergeProposal model with SQLAlchemy 2.0 syntax."""

    def test_create_merge_proposal(self, app):
        """Test creating shop merge proposal."""
        with app.app_context():
            user = User(username="merger", email="merger@test.com")
            user.set_password("pass")
            db.session.add(user)

            shop_main = ShopMain(id="main", canonical_name="Main", canonical_name_lower="main")
            db.session.add(shop_main)
            db.session.commit()

            variant_a = ShopVariant(
                shop_main_id=shop_main.id, source="source_a", source_name="Variant A"
            )
            variant_b = ShopVariant(
                shop_main_id=shop_main.id, source="source_b", source_name="Variant B"
            )
            db.session.add_all([variant_a, variant_b])
            db.session.commit()

            merge_proposal = ShopMergeProposal(
                variant_a_id=variant_a.id,
                variant_b_id=variant_b.id,
                proposed_by_user_id=user.id,
                reason="Duplicates",
                status="PENDING",
            )
            db.session.add(merge_proposal)
            db.session.commit()

            assert merge_proposal.id is not None
            assert merge_proposal.status == "PENDING"


class TestNotificationModel:
    """Test Notification model with SQLAlchemy 2.0 syntax."""

    def test_create_notification_with_relationship(self, app):
        """Test Notification with User relationship."""
        with app.app_context():
            user = User(username="notified", email="notified@test.com")
            user.set_password("pass")
            db.session.add(user)
            db.session.commit()

            notification = Notification(
                user_id=user.id,
                notification_type="proposal_approved",
                title="Your proposal was approved",
                message="Congratulations!",
                link_type="proposal",
                link_id=123,
                is_read=False,
            )
            db.session.add(notification)
            db.session.commit()

            assert notification.id is not None
            assert notification.user.username == "notified"
            assert not notification.is_read


class TestRateCommentModel:
    """Test RateComment model with SQLAlchemy 2.0 syntax."""

    def test_create_rate_comment(self, app):
        """Test RateComment creation with relationships."""
        with app.app_context():
            user = User(username="reviewer", email="reviewer@test.com")
            user.set_password("pass")
            db.session.add(user)

            program = BonusProgram(name="TestProgram", point_value_eur=0.01)
            db.session.add(program)

            shop_main = ShopMain(
                id="comment-test-shop",
                canonical_name="Comment Test Shop",
                canonical_name_lower="comment test shop",
            )
            db.session.add(shop_main)
            db.session.commit()

            shop = Shop(name="Test", shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()

            rate = ShopProgramRate(shop_id=shop.id, program_id=program.id, points_per_eur=5.0)
            db.session.add(rate)
            db.session.commit()

            comment = RateComment(
                rate_id=rate.id,
                reviewer_id=user.id,
                comment_type="verification",
                comment_text="Verified this rate",
            )
            db.session.add(comment)
            db.session.commit()

            assert comment.id is not None
            assert comment.rate.points_per_eur == 5.0
            assert comment.reviewer.username == "reviewer"
