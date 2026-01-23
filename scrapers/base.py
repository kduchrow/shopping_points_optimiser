# noqa: E402
import logging
import os
import sys
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spo.extensions import db  # noqa: E402
from spo.models import Shop, ShopCategory, ShopProgramRate, utcnow  # noqa: E402
from spo.services.bonus_programs import ensure_program  # noqa: E402
from spo.services.dedup import get_or_create_shop_main  # noqa: E402

logger = logging.getLogger("BaseScraper")


class BaseScraper(ABC):
    @abstractmethod
    def fetch(self):
        """Return shop data dict:
        {
          'name': 'ShopName',
          'rates': [
            {'program': 'Payback', 'points_per_eur': 1.0, 'cashback_pct': 0.0, 'point_value_eur': 0.005},
          ]
        }
        """

    def register_to_db(self, data):
        """Register shop and rates to database using ShopMain + ShopVariant deduplication"""

        # Get or create ShopMain with automatic deduplication
        shop_main, is_new, confidence = get_or_create_shop_main(
            shop_name=data["name"], source=self.__class__.__name__, source_id=data.get("source_id")
        )

        # Prevent duplicate ShopVariant insert (defensive, in case dedup logic missed)
        from spo.models import ShopVariant

        existing_variant = ShopVariant.query.filter_by(
            shop_main_id=shop_main.id,
            source=self.__class__.__name__,
            source_id=data.get("source_id"),
        ).first()
        if not existing_variant:
            # Only create ShopVariant if not present
            variant = ShopVariant(
                shop_main_id=shop_main.id,
                source=self.__class__.__name__,
                source_name=data["name"],
                source_id=data.get("source_id"),
                confidence_score=confidence,
            )
            db.session.add(variant)
            db.session.commit()

        # For backward compatibility, get or create legacy Shop table entry
        shop = Shop.query.filter_by(shop_main_id=shop_main.id).first()
        if not shop:
            shop = Shop(name=data["name"], shop_main_id=shop_main.id)
            db.session.add(shop)
            db.session.commit()

        now = utcnow()
        flagged = False
        name_l = (data.get("name") or "").lower()
        if "o2" in name_l or "vodafone" in name_l:
            flagged = True

        for r in data.get("rates", []):
            prog = ensure_program(r["program"], point_value_eur=r.get("point_value_eur", 0.0))

            category_name = r.get("category")
            category_id = None
            if category_name:
                cat = ShopCategory.query.filter_by(name=category_name).first()
                if not cat:
                    cat = ShopCategory(name=category_name)
                    db.session.add(cat)
                    db.session.commit()
                category_id = cat.id

            if flagged:
                logger.info("ShoopDebug rate_payload=%s", r)
                logger.info(
                    "ShoopDebug incoming shop=%s program=%s cat=%s rate_type=%s note_snippet=%s",
                    data.get("name"),
                    r.get("program"),
                    category_name,
                    r.get("rate_type"),
                    (r.get("rate_note") or "")[:200],
                )

            existing = ShopProgramRate.query.filter_by(
                shop_id=shop.id, program_id=prog.id, category_id=category_id, valid_to=None
            ).first()

            fallback_used = False

            # Fallback: if we didn't find a match (e.g., legacy category None) and the incoming
            # rate_type or rate_note differs, try to upgrade the active rate for this shop/program.
            # This handles cases where historical rates need contract type updates.
            if not existing and r.get("rate_type") in {"contract", "shop"}:
                fallback = (
                    ShopProgramRate.query.filter_by(
                        shop_id=shop.id, program_id=prog.id, valid_to=None
                    )
                    .order_by(ShopProgramRate.valid_from.desc())
                    .first()
                )
                if fallback:
                    # Update if rate_type differs OR if rate_note differs (may indicate contract status change)
                    if getattr(fallback, "rate_type", "shop") != r.get("rate_type") or getattr(
                        fallback, "rate_note", None
                    ) != r.get("rate_note"):
                        existing = fallback
                        fallback_used = True
                        # If the new payload has no category, inherit the existing category
                        if category_id is None:
                            category_id = getattr(fallback, "category_id", None)

            if flagged:
                logger.info(
                    "ShoopDebug match shop=%s program=%s cat=%s existing_id=%s fallback_used=%s existing_type=%s",
                    data.get("name"),
                    r.get("program"),
                    category_name,
                    getattr(existing, "id", None),
                    fallback_used,
                    getattr(existing, "rate_type", None),
                )

            new_points = r.get("points_per_eur", 0.0)
            new_cashback = r.get("cashback_pct", 0.0)
            new_points_abs = r.get("points_absolute", None)
            new_cashback_abs = r.get("cashback_absolute", None)
            new_rate_type = r.get("rate_type", "shop")
            new_rate_note = r.get("rate_note", None)

            if not existing:
                new_rate = ShopProgramRate(
                    shop_id=shop.id,
                    program_id=prog.id,
                    points_per_eur=new_points,
                    cashback_pct=new_cashback,
                    points_absolute=new_points_abs,
                    cashback_absolute=new_cashback_abs,
                    rate_type=new_rate_type,
                    rate_note=new_rate_note,
                    category_id=category_id,
                    valid_from=now,
                    valid_to=None,
                )
                db.session.add(new_rate)
                if flagged:
                    logger.info(
                        "ShoopDebug create shop=%s program=%s cat=%s rate_type=%s note_snippet=%s",
                        data.get("name"),
                        r.get("program"),
                        category_name,
                        new_rate_type,
                        (new_rate_note or "")[:200],
                    )
            else:
                # Also check absolute fields for changes
                if (
                    existing.points_per_eur != new_points
                    or existing.cashback_pct != new_cashback
                    or (getattr(existing, "points_absolute", None) != new_points_abs)
                    or (getattr(existing, "cashback_absolute", None) != new_cashback_abs)
                    or (getattr(existing, "rate_type", "shop") != new_rate_type)
                ):
                    existing.valid_to = now
                    db.session.merge(existing)
                    new_rate = ShopProgramRate(
                        shop_id=shop.id,
                        program_id=prog.id,
                        points_per_eur=new_points,
                        cashback_pct=new_cashback,
                        points_absolute=new_points_abs,
                        cashback_absolute=new_cashback_abs,
                        rate_type=new_rate_type,
                        rate_note=new_rate_note,
                        category_id=category_id,
                        valid_from=now,
                        valid_to=None,
                    )
                    db.session.add(new_rate)
                    if flagged:
                        logger.info(
                            "ShoopDebug update shop=%s program=%s cat=%s old_type=%s new_type=%s old_note_snip=%s new_note_snip=%s",
                            data.get("name"),
                            r.get("program"),
                            category_name,
                            getattr(existing, "rate_type", None),
                            new_rate_type,
                            (getattr(existing, "rate_note", "") or "")[:200],
                            (new_rate_note or "")[:200],
                        )

        db.session.commit()
