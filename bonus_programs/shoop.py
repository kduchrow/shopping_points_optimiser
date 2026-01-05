from models import db, BonusProgram

def register():
    prog = BonusProgram.query.filter_by(name='Shoop').first()
    if not prog:
        prog = BonusProgram(name='Shoop', point_value_eur=0.008)  # 1 point = €0.008
        db.session.add(prog)
        db.session.commit()
