"""Test coupon display functionality on web interface"""
from datetime import timedelta
import uuid

from spo.models import BonusProgram, Coupon, Shop, ShopMain, ShopProgramRate, utcnow
from spo.extensions import db


def test_coupon_creation_and_display(app):
    """Test creating a 20x Amazon coupon and verifying it's queryable for display"""
    with app.app_context():
        # Ensure Payback program exists
        payback = BonusProgram.query.filter_by(name='Payback').first()
        if not payback:
            payback = BonusProgram(name='Payback', point_value_eur=0.005)
            db.session.add(payback)
            db.session.commit()

        # Create Amazon shop
        amazon_main = ShopMain(id=str(uuid.uuid4()), canonical_name='Amazon', canonical_name_lower='amazon')
        db.session.add(amazon_main)
        db.session.commit()

        amazon = Shop(name='Amazon', shop_main_id=amazon_main.id)
        db.session.add(amazon)
        db.session.commit()

        # Add a base rate for Amazon
        rate = ShopProgramRate(
            shop_id=amazon.id,
            program_id=payback.id,
            points_per_eur=1.0,
            cashback_pct=0.0,
            valid_from=utcnow(),
            valid_to=None,
        )
        db.session.add(rate)
        db.session.commit()

        # Create 20x coupon for Amazon
        now = utcnow()
        coupon = Coupon(
            name='20-fach Punkte Amazon',
            description='20-fach Payback Punkte bei Einkauf ab 50€',
            coupon_type='multiplier',
            value=20.0,
            shop_id=amazon.id,
            program_id=payback.id,
            valid_from=now,
            valid_to=now + timedelta(days=30),
            status='active',
            combinable=False,
        )
        db.session.add(coupon)
        db.session.commit()

        # Verify coupon is in database
        saved_coupon = Coupon.query.filter_by(name='20-fach Punkte Amazon').one()
        assert saved_coupon.value == 20.0
        assert saved_coupon.coupon_type == 'multiplier'
        assert saved_coupon.status == 'active'
        assert saved_coupon.shop_id == amazon.id
        assert saved_coupon.program_id == payback.id

        # Verify coupon is queryable as would be done in public.py route
        active_coupons = Coupon.query.filter(
            db.or_(Coupon.shop_id == amazon.id, Coupon.shop_id.is_(None)),
            Coupon.status == 'active',
            Coupon.valid_from <= now,
            Coupon.valid_to >= now,
        ).all()

        assert len(active_coupons) == 1
        assert active_coupons[0].name == '20-fach Punkte Amazon'

        # Test coupon logic: 100€ spend should give 20x points
        amount = 100.0
        base_points = amount * rate.points_per_eur  # 100 points
        program_coupons = [c for c in active_coupons if c.program_id in (None, payback.id)]
        best_coupon = max((c.value for c in program_coupons if c.coupon_type == 'multiplier'), default=1)

        assert best_coupon == 20.0
        coupon_points = base_points * best_coupon  # 100 * 20 = 2000
        assert coupon_points == 2000.0
        coupon_euros = coupon_points * payback.point_value_eur  # 2000 * 0.005 = 10€
        assert coupon_euros == 10.0


def test_coupon_display_in_evaluate_route(app, client):
    """Test that coupon appears in evaluate endpoint response"""
    with app.app_context():
        # Setup: Create Payback, Amazon, rate, and 20x coupon
        payback = BonusProgram.query.filter_by(name='Payback').first()
        if not payback:
            payback = BonusProgram(name='Payback', point_value_eur=0.005)
            db.session.add(payback)
            db.session.commit()

        amazon_main = ShopMain(id=str(uuid.uuid4()), canonical_name='Amazon', canonical_name_lower='amazon')
        db.session.add(amazon_main)
        db.session.commit()

        amazon = Shop(name='Amazon', shop_main_id=amazon_main.id)
        db.session.add(amazon)
        db.session.commit()

        rate = ShopProgramRate(
            shop_id=amazon.id,
            program_id=payback.id,
            points_per_eur=1.0,
            cashback_pct=0.0,
            valid_from=utcnow(),
            valid_to=None,
        )
        db.session.add(rate)
        db.session.commit()

        now = utcnow()
        coupon = Coupon(
            name='20-fach Punkte Amazon',
            description='20-fach Payback Punkte bei Einkauf ab 50€',
            coupon_type='multiplier',
            value=20.0,
            shop_id=amazon.id,
            program_id=payback.id,
            valid_from=now,
            valid_to=now + timedelta(days=30),
            status='active',
            combinable=False,
        )
        db.session.add(coupon)
        db.session.commit()

        amazon_id = amazon.id  # Store ID before leaving app_context

    # Make request to evaluate endpoint
    response = client.post('/evaluate', data={
        'mode': 'shopping',
        'shop': amazon_id,
        'amount': 100.0,
    })

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    # Verify coupon appears in response HTML
    assert '20-fach Punkte Amazon' in html
    assert '20-fach Payback Punkte bei Einkauf ab 50€' in html
    assert 'Verfügbare Sonderaktionen' in html or 'active_coupons' in html
    # Verify multiplier display
    assert '20x' in html or '×20' in html
