from spo.extensions import db
from spo.models import BonusProgram, Shop, ShopMain, ShopVariant, User
from spo.services.bonus_programs import ensure_program
from spo.services.dedup import find_duplicate_shops, get_or_create_shop_main, run_deduplication
from spo.services.notifications import (
    create_notification,
    get_unread_count,
    mark_all_as_read,
    mark_as_read,
)
from spo.utils import ensure_variant_for_shop


def _create_user(session, username="tester"):
    user = User(username=username, email=f"{username}@local", role="viewer", status="active")
    user.set_password("pw")
    session.add(user)
    session.commit()
    return user


def test_dedup_merges_case_insensitive(app, session):
    with app.app_context():
        main1, created1, score1 = get_or_create_shop_main("Amazon", "source_a", "id-1")
        main2, created2, score2 = get_or_create_shop_main("amazon", "source_b", "id-2")

        assert created1 is True
        assert created2 is False
        assert main1.id == main2.id
        assert score1 >= 98.0 and score2 >= 98.0

        variants = ShopVariant.query.filter_by(shop_main_id=main1.id).all()
        assert len(variants) == 2
        assert {v.source for v in variants} == {"source_a", "source_b"}


def test_notifications_create_and_mark_read(app, session):
    with app.app_context():
        user = _create_user(session)
        notif = create_notification(
            user_id=user.id,
            notification_type="TEST",
            title="Hello",
            message="World",
        )

        assert notif.id is not None
        assert get_unread_count(user.id) == 1

        assert mark_as_read(notif.id, user.id) is True
        assert get_unread_count(user.id) == 0

        # create multiple and mark all
        create_notification(user.id, "TEST", "A", "a")
        create_notification(user.id, "TEST", "B", "b")
        assert get_unread_count(user.id) == 2
        mark_all_as_read(user.id)
        assert get_unread_count(user.id) == 0


def test_ensure_program_creates_and_updates(app, session):
    with app.app_context():
        prog = ensure_program("MilesAndMore", 0.01)
        assert prog.point_value_eur == 0.01

        prog_updated = ensure_program("MilesAndMore", 0.02)
        assert prog_updated.id == prog.id
        assert prog_updated.point_value_eur == 0.02

        # second call with same value should not create new row
        assert BonusProgram.query.filter_by(name="MilesAndMore").count() == 1


def test_ensure_variant_for_shop_creates_once(app, session):
    with app.app_context():
        main = ShopMain(
            id="main-1", canonical_name="Demo", canonical_name_lower="demo", status="active"
        )
        db.session.add(main)
        db.session.flush()

        shop = Shop(name="Demo", shop_main_id=main.id)
        db.session.add(shop)
        db.session.commit()

        first = ensure_variant_for_shop(shop)
        second = ensure_variant_for_shop(shop)

        assert first.id == second.id
        variants = ShopVariant.query.filter_by(shop_main_id=main.id, source="manual").all()
        assert len(variants) == 1
        assert variants[0].source_name == "Demo"


def test_find_duplicate_shops(app, session):
    """Test finding duplicate shops based on similarity."""
    with app.app_context():
        # Create duplicate shops manually (bypassing dedup logic)
        shop1 = ShopMain(
            id="shop-1",
            canonical_name="Amazon",
            canonical_name_lower="amazon",
            status="active",
        )
        shop2 = ShopMain(
            id="shop-2",
            canonical_name="amazon",
            canonical_name_lower="amazon",
            status="active",
        )
        shop3 = ShopMain(
            id="shop-3",
            canonical_name="Walmart",
            canonical_name_lower="walmart",
            status="active",
        )
        db.session.add_all([shop1, shop2, shop3])
        db.session.commit()

        duplicates = find_duplicate_shops(threshold=98.0)

        assert len(duplicates) == 1
        assert duplicates[0][2] >= 98.0  # similarity score
        # Check that the duplicate pair contains Amazon shops
        duplicate_names = {duplicates[0][0].canonical_name, duplicates[0][1].canonical_name}
        assert duplicate_names == {"Amazon", "amazon"}


def test_run_deduplication(app, session):
    """Test automatic deduplication of shops."""
    with app.app_context():
        user = _create_user(session, "admin_user")

        # Create duplicate shops manually
        shop1 = ShopMain(
            id="shop-1",
            canonical_name="Amazon",
            canonical_name_lower="amazon",
            status="active",
        )
        shop2 = ShopMain(
            id="shop-2",
            canonical_name="amazon",
            canonical_name_lower="amazon",
            status="active",
        )
        db.session.add_all([shop1, shop2])
        db.session.commit()

        # Add variants to track them
        variant1 = ShopVariant(
            shop_main_id=shop1.id,
            source="source_a",
            source_name="Amazon",
            source_id="id-1",
            confidence_score=100.0,
        )
        variant2 = ShopVariant(
            shop_main_id=shop2.id,
            source="source_b",
            source_name="amazon",
            source_id="id-2",
            confidence_score=100.0,
        )
        db.session.add_all([variant1, variant2])
        db.session.commit()

        # Run deduplication
        result = run_deduplication(system_user_id=user.id)

        assert result["merged_count"] == 1
        assert result["duplicates_found"] == 1
        assert len(result["errors"]) == 0

        # Verify one shop is now merged
        active_shops = ShopMain.query.filter_by(status="active").all()
        merged_shops = ShopMain.query.filter_by(status="merged").all()

        assert len(active_shops) == 1
        assert len(merged_shops) == 1

        # Verify all variants point to the active shop
        all_variants = ShopVariant.query.all()
        assert len(all_variants) == 2
        assert all(v.shop_main_id == active_shops[0].id for v in all_variants)
