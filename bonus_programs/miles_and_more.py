from models import db, BonusProgram, ShopProgramRate, Shop

def register():
    # Miles & More - example values
    prog = BonusProgram.query.filter_by(name='MilesAndMore').first()
    if not prog:
        prog = BonusProgram(name='MilesAndMore', point_value_eur=0.01)  # 1 point = €0.01
        db.session.add(prog)
        db.session.commit()
