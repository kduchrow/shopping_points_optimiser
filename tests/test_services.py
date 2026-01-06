from spo.extensions import db
from spo.models import BonusProgram, Shop, ShopMain, ShopVariant, User
from spo.services.bonus_programs import ensure_program
from spo.services.dedup import get_or_create_shop_main
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
