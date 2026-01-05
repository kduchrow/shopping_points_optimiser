"""Bonus program helpers and seeders."""

from spo.extensions import db
from spo.models import BonusProgram


DEFAULT_PROGRAMS = {
    'MilesAndMore': 0.01,
    'Payback': 0.005,
    'Shoop': 0.008,
}


def ensure_program(name: str, point_value_eur: float = 0.0) -> BonusProgram:
    """Ensure a BonusProgram exists and optionally refresh its point value."""
    program = BonusProgram.query.filter_by(name=name).first()
    if not program:
        program = BonusProgram(name=name, point_value_eur=point_value_eur)
        db.session.add(program)
    elif point_value_eur is not None and program.point_value_eur != point_value_eur:
        program.point_value_eur = point_value_eur
    db.session.commit()
    return program


def register_defaults() -> None:
    """Seed the default bonus programs if missing."""
    for name, value in DEFAULT_PROGRAMS.items():
        ensure_program(name, value)
