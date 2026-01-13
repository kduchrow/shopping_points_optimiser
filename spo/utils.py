from spo.extensions import db
from spo.models import Shop, ShopVariant


def ensure_variant_for_shop(shop: Shop) -> ShopVariant:
    existing = ShopVariant.query.filter_by(
        shop_main_id=shop.shop_main_id, source="manual", source_name=shop.name
    ).first()
    if existing:
        return existing
    variant = ShopVariant(
        shop_main_id=shop.shop_main_id,
        source="manual",
        source_name=shop.name,
        source_id=str(shop.id),
        confidence_score=100.0,
    )
    db.session.add(variant)
    db.session.commit()
    return variant
