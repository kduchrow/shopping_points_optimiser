from datetime import datetime, timedelta

from app import app
from spo.extensions import db
from spo.models import Coupon, Shop

app.app_context().push()

# Get a shop (Payback if available)
shop = Shop.query.first()
if not shop:
    print("Keine Shops vorhanden!")
else:
    # Create a test coupon
    coupon = Coupon(
        coupon_type="multiplier",
        name="20x Punkte Test",
        description="20-fach Punkte beim Einkauf",
        value=20.0,
        combinable=True,
        shop_id=shop.id,
        program_id=None,  # For all programs
        valid_from=datetime.utcnow(),
        valid_to=datetime.utcnow() + timedelta(days=30),
        status="active",
    )
    db.session.add(coupon)
    db.session.commit()
    print(f"✓ Test-Coupon erstellt: {coupon.name} für {shop.name}")
    print(f"  Type: {coupon.coupon_type} x{coupon.value}")
    print(f"  Gültig bis: {coupon.valid_to.strftime('%d.%m.%Y')}")
