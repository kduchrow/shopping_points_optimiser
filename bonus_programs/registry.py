from spo.extensions import db
from spo.models import BonusProgram


def get_or_create_program(name: str, point_value_eur: float = 0.0) -> BonusProgram:
    prog = BonusProgram.query.filter_by(name=name).first()
    if not prog:
        prog = BonusProgram(name=name, point_value_eur=point_value_eur)
        db.session.add(prog)
        db.session.commit()
    return prog
