"""Seed helper functions."""

from spo.extensions import db
from spo.models import BonusProgram, Shop, ShopProgramRate
from spo.services.bonus_programs import ensure_program


def register_example_shop() -> None:
    """Create a demo shop with baseline rates for known programs."""
    ensure_program("MilesAndMore", 0.01)
    ensure_program("Payback", 0.005)
    ensure_program("Shoop", 0.008)

    shop = Shop.query.filter_by(name="ExampleShop").first()
    if not shop:
        shop = Shop(name="ExampleShop")
        db.session.add(shop)
        db.session.commit()

    rates = {
        "MilesAndMore": {"points_per_eur": 0.5, "cashback_pct": 0.0},
        "Payback": {"points_per_eur": 1.0, "cashback_pct": 0.0},
        "Shoop": {"points_per_eur": 0.75, "cashback_pct": 2.0},
    }

    for program_name, values in rates.items():
        program = BonusProgram.query.filter_by(name=program_name).first()
        if not program:
            continue
        existing = ShopProgramRate.query.filter_by(shop_id=shop.id, program_id=program.id).first()
        if existing:
            continue
        db.session.add(
            ShopProgramRate(
                shop_id=shop.id,
                program_id=program.id,
                points_per_eur=values["points_per_eur"],
                cashback_pct=values["cashback_pct"],
            )
        )

    db.session.commit()
