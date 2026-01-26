"""Shop deduplication and similarity scoring utilities."""

import re
import uuid
from datetime import UTC, datetime
from difflib import SequenceMatcher

from spo.extensions import db
from spo.models import ShopMain, ShopVariant


def _normalize_shop_name(name: str) -> str:
    """Normalize a shop name to improve fuzzy matching.

    - Lowercase and trim
    - Strip protocols and common domain noise (www., TLDs)
    - Remove generic tokens like 'online', 'shop', 'store', 'club'
    - Collapse punctuation and whitespace to single spaces
    """
    s = name.lower().strip()

    # Remove protocol prefixes
    s = re.sub(r"^(https?://)", "", s)
    s = re.sub(r"^www\.", "", s)

    # If domain-like (no spaces, has dots), extract main label before TLD
    if " " not in s and "." in s:
        parts = s.split(".")
        # Drop leading 'www' and trailing TLDs
        parts = [p for p in parts if p and p not in {"www", "com", "de", "net", "org", "eu"}]
        if parts:
            s = " ".join(parts)

    # Replace punctuation with spaces
    s = re.sub(r"[\-_/&|,:;.!?\"'()+]", " ", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    # Remove generic tokens
    stop = {
        "online",
        "onlineshop",
        "shop",
        "store",
        "club",
        "produkte",
        "gutscheine",
        "official",
    }
    tokens = [t for t in s.split(" ") if t and t not in stop]
    return " ".join(tokens)


def fuzzy_match_score(str1: str, str2: str) -> float:
    """Calculate similarity score between two strings (0-100)."""
    s1 = _normalize_shop_name(str1)
    s2 = _normalize_shop_name(str2)

    if not s1 or not s2:
        return 0.0

    # Only treat as 100% match if normalized names are exactly equal (case/space insensitive)
    if s1.replace(" ", "") == s2.replace(" ", ""):
        return 100.0

    # For substring matches, require at least 2 token overlap to avoid over-merging (e.g., 'otto' vs 'ottonova')
    tokens1 = set(s1.split())
    tokens2 = set(s2.split())
    common_tokens = tokens1 & tokens2
    if (s1 in s2 or s2 in s1) and len(common_tokens) >= 2:
        return 98.0

    ratio = SequenceMatcher(None, s1, s2).ratio()
    return round(ratio * 100, 1)


def find_shop_by_similarity(shop_name: str, threshold: float = 98.0) -> tuple:
    """Find existing ShopMain candidates by similarity score."""
    all_shops = ShopMain.query.all()

    best_match = None
    best_score = 0.0

    for shop in all_shops:
        score = fuzzy_match_score(shop_name, shop.canonical_name)
        if score > best_score:
            best_score = score
            best_match = shop

    if best_score >= threshold:
        return best_match, best_score

    return None, best_score


def get_or_create_shop_main(shop_name: str, source: str, source_id: str | None = None) -> tuple:
    """Get or create a ShopMain entry with automatic deduplication."""
    existing_shop, score = find_shop_by_similarity(shop_name, threshold=0)

    if score >= 98.0:
        # Check for existing variant with same source and source_id
        existing_variant = ShopVariant.query.filter_by(
            shop_main_id=existing_shop.id, source=source, source_id=source_id
        ).first()
        if not existing_variant:
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
            status="active",
        )
        db.session.add(new_main_shop)
        db.session.flush()

        existing_variant = ShopVariant.query.filter_by(
            shop_main_id=new_main_shop.id, source=source, source_id=source_id
        ).first()
        if not existing_variant:
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
        status="active",
    )
    db.session.add(new_main_shop)
    db.session.flush()

    existing_variant = ShopVariant.query.filter_by(
        shop_main_id=new_main_shop.id, source=source, source_id=source_id
    ).first()
    if not existing_variant:
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
    """Merge one shop into another and re-point variants and Shop entries."""
    from spo.models import Shop

    from_shop = db.session.get(ShopMain, main_from_id)
    to_shop = db.session.get(ShopMain, main_to_id)

    if not from_shop or not to_shop:
        raise ValueError("One or both shops not found")

    # Move all ShopVariants to the target ShopMain
    variants = list(from_shop.variants) if hasattr(from_shop.variants, "__iter__") else []
    for variant in variants:
        variant.shop_main_id = to_shop.id

    # Move all Shop entries to the target ShopMain
    Shop.query.filter_by(shop_main_id=main_from_id).update({"shop_main_id": main_to_id})

    from_shop.status = "merged"
    from_shop.merged_into_id = main_to_id
    from_shop.updated_at = datetime.now(UTC)
    from_shop.updated_by_user_id = user_id

    db.session.commit()


def find_duplicate_shops(threshold: float = 98.0) -> list[tuple]:
    """Find duplicate shops based on similarity score.

    Returns a list of tuples (shop1, shop2, similarity_score) where shops are duplicates.
    """
    active_shops = ShopMain.query.filter_by(status="active").all()
    duplicates = []

    for i, shop1 in enumerate(active_shops):
        for shop2 in active_shops[i + 1 :]:
            score = fuzzy_match_score(shop1.canonical_name, shop2.canonical_name)
            if score >= threshold:
                duplicates.append((shop1, shop2, score))

    return duplicates


def run_deduplication(
    job=None, auto_merge_threshold: float = 98.0, system_user_id: int | None = None
):
    """Find and merge duplicate shops automatically.

    Args:
        job: Optional Job object to report progress
        auto_merge_threshold: Similarity threshold for automatic merging (default 98.0)
        system_user_id: User ID to attribute merges to (default None for system)

    Returns:
        dict with summary of merges performed
    """
    if job:
        job.add_message("Starting deduplication scan...")
        job.set_progress(0, 100)

    duplicates = find_duplicate_shops(threshold=auto_merge_threshold)

    if job:
        job.add_message(f"Found {len(duplicates)} duplicate pairs to merge")
        job.set_progress(20, 100)

    merged_count = 0
    errors = []

    for idx, (shop1, shop2, score) in enumerate(duplicates):
        try:
            # Merge into the shop that was created first (older shop)
            if shop1.created_at <= shop2.created_at:
                target_shop = shop1
                source_shop = shop2
            else:
                target_shop = shop2
                source_shop = shop1

            # Skip if already merged
            if source_shop.status != "active":
                continue

            merge_shops(
                main_from_id=source_shop.id, main_to_id=target_shop.id, user_id=system_user_id or 0
            )

            merged_count += 1
            if job:
                msg = f"Merged '{source_shop.canonical_name}' into '{target_shop.canonical_name}' (score: {score})"
                job.add_message(msg)
                progress = 20 + int((idx + 1) / len(duplicates) * 70)
                job.set_progress(progress, 100)

        except Exception as e:
            error_msg = f"Error merging {shop1.canonical_name} and {shop2.canonical_name}: {str(e)}"
            errors.append(error_msg)
            if job:
                job.add_message(f"ERROR: {error_msg}")

    if job:
        job.add_message(f"Deduplication complete. Merged {merged_count} duplicate shops.")
        job.set_progress(100, 100)

    return {"merged_count": merged_count, "duplicates_found": len(duplicates), "errors": errors}


def split_shop_variants(
    shop_main_id: str, variant_ids: list[int], new_shop_name: str, user_id: int
) -> str:
    """Split variants from a ShopMain into a new ShopMain.

    Args:
        shop_main_id: ID of the source ShopMain
        variant_ids: List of ShopVariant IDs to move to the new ShopMain
        new_shop_name: Name for the new ShopMain
        user_id: User ID performing the split

    Returns:
        ID of the newly created ShopMain
    """

    source_shop = db.session.get(ShopMain, shop_main_id)
    if not source_shop:
        raise ValueError(f"ShopMain {shop_main_id} not found")

    # Validate that all variants belong to the source shop
    variants_to_move = []
    for variant_id in variant_ids:
        variant = db.session.get(ShopVariant, variant_id)
        if not variant:
            raise ValueError(f"ShopVariant {variant_id} not found")
        if variant.shop_main_id != shop_main_id:
            raise ValueError(f"ShopVariant {variant_id} does not belong to ShopMain {shop_main_id}")
        variants_to_move.append(variant)

    if not variants_to_move:
        raise ValueError("No variants to split")

    # Create new ShopMain
    new_shop_main = ShopMain(
        id=str(uuid.uuid4()),
        canonical_name=new_shop_name,
        canonical_name_lower=new_shop_name.lower(),
        website=None,
        logo_url=None,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        updated_by_user_id=user_id,
    )
    db.session.add(new_shop_main)

    # Move variants to new ShopMain
    for variant in variants_to_move:
        variant.shop_main_id = new_shop_main.id

    # Note: Shop entries remain with the source ShopMain
    # If needed, admin can manually reassign Shop entries later
    # or we can add logic to automatically create new Shop entries

    db.session.commit()

    return new_shop_main.id
