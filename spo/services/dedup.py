"""Shop deduplication and similarity scoring utilities."""

import uuid
from difflib import SequenceMatcher
from datetime import UTC, datetime

from spo.extensions import db
from spo.models import ShopMain, ShopVariant


def fuzzy_match_score(str1: str, str2: str) -> float:
    """Calculate similarity score between two strings (0-100)."""
    s1 = str1.lower().strip()
    s2 = str2.lower().strip()

    for char in ['-', '_', '.', ',', '&', '!', '?', "'", '"']:
        s1 = s1.replace(char, '')
        s2 = s2.replace(char, '')

    ratio = SequenceMatcher(None, s1, s2).ratio()
    return round(ratio * 100, 1)


def find_shop_by_similarity(shop_name: str, threshold: float = 98.0) -> tuple:
    """Find existing ShopMain candidates by similarity score."""
    all_shops = ShopMain.query.all()

    best_match = None
    best_score = 0

    for shop in all_shops:
        score = fuzzy_match_score(shop_name, shop.canonical_name)
        if score > best_score:
            best_score = score
            best_match = shop

    if best_score >= threshold:
        return best_match, best_score

    return None, best_score


def get_or_create_shop_main(shop_name: str, source: str, source_id: str = None) -> tuple:
    """Get or create a ShopMain entry with automatic deduplication."""
    existing_shop, score = find_shop_by_similarity(shop_name, threshold=0)

    if score >= 98.0:
        variant = ShopVariant(
            shop_main_id=existing_shop.id,
            source=source,
            source_name=shop_name,
            source_id=source_id,
            confidence_score=100.0,
        )
        db.session.add(variant)
        db.session.commit()
        return existing_shop, False, 100.0

    if 70.0 <= score < 98.0:
        new_main_shop = ShopMain(
            id=str(uuid.uuid4()),
            canonical_name=shop_name,
            canonical_name_lower=shop_name.lower(),
            status='active',
        )
        db.session.add(new_main_shop)
        db.session.flush()

        variant = ShopVariant(
            shop_main_id=new_main_shop.id,
            source=source,
            source_name=shop_name,
            source_id=source_id,
            confidence_score=score,
        )
        db.session.add(variant)
        db.session.commit()

        return new_main_shop, True, score

    new_main_shop = ShopMain(
        id=str(uuid.uuid4()),
        canonical_name=shop_name,
        canonical_name_lower=shop_name.lower(),
        status='active',
    )
    db.session.add(new_main_shop)
    db.session.flush()

    variant = ShopVariant(
        shop_main_id=new_main_shop.id,
        source=source,
        source_name=shop_name,
        source_id=source_id,
        confidence_score=100.0,
    )
    db.session.add(variant)
    db.session.commit()

    return new_main_shop, True, 100.0


def merge_shops(main_from_id: str, main_to_id: str, user_id: int):
    """Merge one shop into another and re-point variants."""
    from_shop = ShopMain.query.get(main_from_id)
    to_shop = ShopMain.query.get(main_to_id)

    if not from_shop or not to_shop:
        raise ValueError("One or both shops not found")

    for variant in from_shop.variants:
        variant.shop_main_id = to_shop.id

    from_shop.status = 'merged'
    from_shop.merged_into_id = main_to_id
    from_shop.updated_at = datetime.now(UTC)
    from_shop.updated_by_user_id = user_id

    db.session.commit()
