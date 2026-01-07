"""
Test admin endpoint to rescore ShopVariant confidence scores.
"""

from spo import create_app
from spo.extensions import db
from spo.models import Shop, ShopMain, ShopVariant


def test_admin_rescore_variants(client, admin_user):
    app = create_app(start_jobs=False, run_seed=False)
    with app.app_context():
        # Create a main and attach shops/variants simulating noisy names
        main = ShopMain(
            id="mm-main",
            canonical_name="mediamarkt",
            canonical_name_lower="mediamarkt",
            status="active",
        )
        db.session.add(main)
        db.session.commit()

        shop = Shop(name="mediamarkt", shop_main_id=main.id)
        db.session.add(shop)
        db.session.commit()

        v1 = ShopVariant(
            shop_main_id=main.id,
            source="PaybackScraperJS",
            source_name="mediamarkt online shop",
            confidence_score=70.0,
        )
        v2 = ShopVariant(
            shop_main_id=main.id,
            source="user_proposal",
            source_name="mediamarkt.de",
            confidence_score=90.9,
        )
        db.session.add_all([v1, v2])
        db.session.commit()
        v1_id = v1.id
        v2_id = v2.id

    # Login as admin
    client.post(
        "/login",
        data={"username": admin_user.username, "password": admin_user._test_password},
        follow_redirects=True,
    )

    # Call rescore endpoint
    resp = client.post("/admin/variants/rescore", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["updated"] >= 1

    # Verify updated scores are higher and normalized
    with app.app_context():
        v1r = db.session.get(ShopVariant, v1_id)
        v2r = db.session.get(ShopVariant, v2_id)
        assert v1r is not None and v1r.confidence_score >= 95.0
        assert v2r is not None and v2r.confidence_score >= 98.0
