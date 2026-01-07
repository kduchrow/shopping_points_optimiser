"""Test admin clear_shops endpoint with all FK constraints."""


from datetime import datetime, timedelta

from spo.extensions import db
from spo.models import (
    BonusProgram,
    Coupon,
    Proposal,
    Shop,
    ShopMain,
    ShopMergeProposal,
    ShopMetadataProposal,
    ShopProgramRate,
    ShopVariant,
)


def test_clear_shops_with_all_foreign_keys(client, admin_user):
    """Test that clear_shops deletes all shops and related data without FK violations."""
    # Login as admin using credentials from fixture
    client.post(
        "/login",
        data={"username": admin_user.username, "password": admin_user._test_password},
        follow_redirects=True,
    )

    # Create test data with all FK relationships
    # 1. Create ShopMain
    shop_main = ShopMain(
        id="test-main-1",
        canonical_name="Test Shop",
        canonical_name_lower="test shop",
        status="active",
    )
    db.session.add(shop_main)
    db.session.commit()  # Commit ShopMain first for FK references

    # 2. Create ShopVariant (references ShopMain)
    shop_variant = ShopVariant(
        shop_main_id=shop_main.id,
        source="test",
        source_name="Test Shop",
        source_id="test-1",
    )
    db.session.add(shop_variant)

    # 3. Create Shop (references ShopMain)
    shop = Shop(name="Test Shop", shop_main_id=shop_main.id)
    db.session.add(shop)
    db.session.flush()  # Get shop.id

    # 4. Create BonusProgram
    program = BonusProgram(name="Test Program", point_value_eur=0.01)
    db.session.add(program)
    db.session.flush()

    # 5. Create ShopProgramRate (references Shop)
    rate = ShopProgramRate(
        shop_id=shop.id, program_id=program.id, points_per_eur=1.0, cashback_pct=0.0
    )
    db.session.add(rate)

    # 6. Create Proposal (references Shop) - THIS WAS MISSING!
    proposal = Proposal(
        proposal_type="rate",
        status="pending",
        source="user",
        user_id=admin_user.id,
        shop_id=shop.id,
        program_id=program.id,
        proposed_points_per_eur=2.0,
    )
    db.session.add(proposal)

    # 7. Create ShopMetadataProposal (references ShopMain)
    metadata_proposal = ShopMetadataProposal(
        shop_main_id=shop_main.id,
        proposed_name="Updated Name",
        proposed_by_user_id=admin_user.id,
        status="PENDING",
    )
    db.session.add(metadata_proposal)

    # 8. Create another ShopMain and ShopVariant for merge proposal
    shop_main_2 = ShopMain(
        id="test-main-2",
        canonical_name="Test Shop 2",
        canonical_name_lower="test shop 2",
        status="active",
    )
    db.session.add(shop_main_2)

    shop_variant_2 = ShopVariant(
        shop_main_id=shop_main_2.id,
        source="test",
        source_name="Test Shop 2",
        source_id="test-2",
    )
    db.session.add(shop_variant_2)
    db.session.flush()  # Get variant IDs for merge proposal

    # 9. Create ShopMergeProposal (references ShopVariant)
    merge_proposal = ShopMergeProposal(
        variant_a_id=shop_variant.id,
        variant_b_id=shop_variant_2.id,
        proposed_by_user_id=admin_user.id,
        status="PENDING",
    )
    db.session.add(merge_proposal)

    # 10. Create Coupon (references Shop)
    coupon = Coupon(
        shop_id=shop.id,
        name="Test Coupon",
        coupon_type="percentage",
        value=10.0,
        description="Test coupon",
        valid_to=datetime.utcnow() + timedelta(days=30),
    )
    db.session.add(coupon)

    db.session.commit()

    # Verify data exists
    assert Shop.query.count() == 1
    assert ShopMain.query.count() == 2
    assert ShopVariant.query.count() == 2
    assert ShopProgramRate.query.count() == 1
    assert Proposal.query.count() == 1
    assert ShopMetadataProposal.query.count() == 1
    assert ShopMergeProposal.query.count() == 1
    assert Coupon.query.count() == 1

    # Call clear_shops endpoint
    response = client.post("/admin/clear_shops", headers={"Accept": "application/json"})

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["deleted"] == 2  # 2 ShopMains

    # Verify all data is deleted
    assert Shop.query.count() == 0
    assert ShopMain.query.count() == 0
    assert ShopVariant.query.count() == 0
    assert ShopProgramRate.query.count() == 0
    assert Proposal.query.count() == 0
    assert ShopMetadataProposal.query.count() == 0
    assert ShopMergeProposal.query.count() == 0
    assert Coupon.query.count() == 0

    # BonusProgram should remain (not deleted)
    assert BonusProgram.query.count() == 1
