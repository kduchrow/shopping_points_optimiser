from models import db, BonusProgram

def register():
    prog = BonusProgram.query.filter_by(name='Payback').first()
    if not prog:
        prog = BonusProgram(name='Payback', point_value_eur=0.005)  # 1 point = €0.005
        db.session.add(prog)
        db.session.commit()
