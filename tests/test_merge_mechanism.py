"""
Tests for shop merge mechanism and UI support flags.
"""

from spo import create_app
from spo.extensions import db
from spo.models import BonusProgram, Shop, ShopMain, ShopProgramRate, ShopVariant
from spo.services.dedup import merge_shops


def create_shop_with_rate(main_id: str, name: str, program: BonusProgram, ppe: float = 1.0):
    shop = Shop(name=name, shop_main_id=main_id)
    db.session.add(shop)
    db.session.flush()
    rate = ShopProgramRate(
        shop_id=shop.id, program_id=program.id, points_per_eur=ppe, cashback_pct=0.0
    )
    db.session.add(rate)
    return shop


def test_index_supports_flags_across_siblings(client):
    """Index should show support if any sibling shop has rates."""
    app = create_app(start_jobs=False, run_seed=False)
    with app.app_context():
        # Ensure a program exists
        program = BonusProgram.query.first()
        if not program:
            program = BonusProgram(name="Test Program", point_value_eur=0.01)
            db.session.add(program)
            db.session.commit()

        # Create a ShopMain with two shops: one without rates, one with rates
        main = ShopMain(
            id="main-1", canonical_name="Amazon", canonical_name_lower="amazon", status="active"
        )
        db.session.add(main)
        db.session.commit()

        shop_no_rates = Shop(name="Amazon Placeholder", shop_main_id=main.id)
        db.session.add(shop_no_rates)
        db.session.flush()

        create_shop_with_rate(main.id, "Amazon Live", program, ppe=1.0)
        db.session.commit()

        # Query /shop_names with filter for 'amazon'
        resp = client.get("/shop_names", query_string={"q": "amazon"})
        assert resp.status_code == 200
        # Accept both JSON and legacy list response
        try:
            data = resp.get_json()
        except Exception:
            data = resp.json if hasattr(resp, "json") else resp.get_data(as_text=True)

        # If response is a dict with 'shops', use that, else assume list
        if isinstance(data, dict) and "shops" in data:
            shops = data["shops"]
        else:
            shops = data if isinstance(data, list) else []

        assert any("Amazon" in shop["name"] for shop in shops)


def test_merge_moves_shops_and_keeps_target_active(client, admin_user):
    """Merging should move shops to target ShopMain and mark source as merged."""
    app = create_app(start_jobs=False, run_seed=False)
    with app.app_context():
        # Ensure a program exists
        program = BonusProgram.query.first()
        if not program:
            program = BonusProgram(name="Test Program", point_value_eur=0.01)
            db.session.add(program)
            db.session.commit()

        # Create two mains: Amazon (target) and Amazon2 (source)
        amazon = ShopMain(
            id="amazon-main",
            canonical_name="Amazon",
            canonical_name_lower="amazon",
            status="active",
        )
        amazon2 = ShopMain(
            id="amazon2-main",
            canonical_name="Amazon2",
            canonical_name_lower="amazon2",
            status="active",
        )
        db.session.add(amazon)
        db.session.add(amazon2)
        db.session.commit()

        # Create variants
        v1 = ShopVariant(shop_main_id=amazon.id, source="test", source_name="Amazon")
        v2 = ShopVariant(shop_main_id=amazon2.id, source="test", source_name="Amazon2")
        db.session.add_all([v1, v2])
        db.session.commit()

        # Create shops and rates under each
        create_shop_with_rate(amazon.id, "Amazon Live", program, ppe=1.0)
        src_shop = Shop(name="Amazon2 Shop", shop_main_id=amazon2.id)
        db.session.add(src_shop)
        db.session.commit()

        # Merge Amazon2 into Amazon
        merge_shops(main_from_id=amazon2.id, main_to_id=amazon.id, user_id=admin_user.id)

        # Source should be marked merged, target still active
        src_main = db.session.get(ShopMain, amazon2.id)
        tgt_main = db.session.get(ShopMain, amazon.id)
        assert src_main is not None and src_main.status == "merged"
        assert tgt_main is not None and tgt_main.status == "active"

        # Shops under source should now point to target
        shops_under_target = Shop.query.filter_by(shop_main_id=amazon.id).all()
        assert any(s.name == "Amazon2 Shop" for s in shops_under_target)

        # /shop_names should list only active mains (Amazon) and not Amazon2
        resp = client.get("/shop_names", query_string={"q": "amazon"})
        assert resp.status_code == 200
        try:
            data = resp.get_json()
        except Exception:
            data = resp.json if hasattr(resp, "json") else resp.get_data(as_text=True)

        if isinstance(data, dict) and "shops" in data:
            shops = data["shops"]
        else:
            shops = data if isinstance(data, list) else []

        names = [shop["name"] for shop in shops]
        assert any("Amazon" == name for name in names)
        assert all("Amazon2" != name for name in names)
