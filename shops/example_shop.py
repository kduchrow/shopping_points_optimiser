from models import db, Shop, BonusProgram, ShopProgramRate

def register():
    shop = Shop.query.filter_by(name='ExampleShop').first()
    if not shop:
        shop = Shop(name='ExampleShop')
        db.session.add(shop)
        db.session.commit()

    # attach rates for known programs if not present
    prog = BonusProgram.query.filter_by(name='MilesAndMore').first()
    if prog:
        r = ShopProgramRate.query.filter_by(shop_id=shop.id, program_id=prog.id).first()
        if not r:
            r = ShopProgramRate(shop_id=shop.id, program_id=prog.id, points_per_eur=0.5, cashback_pct=0.0)
            db.session.add(r)

    prog = BonusProgram.query.filter_by(name='Payback').first()
    if prog:
        r = ShopProgramRate.query.filter_by(shop_id=shop.id, program_id=prog.id).first()
        if not r:
            r = ShopProgramRate(shop_id=shop.id, program_id=prog.id, points_per_eur=1.0, cashback_pct=0.0)
            db.session.add(r)

    prog = BonusProgram.query.filter_by(name='Shoop').first()
    if prog:
        r = ShopProgramRate.query.filter_by(shop_id=shop.id, program_id=prog.id).first()
        if not r:
            r = ShopProgramRate(shop_id=shop.id, program_id=prog.id, points_per_eur=0.75, cashback_pct=2.0)
            db.session.add(r)

    db.session.commit()
