from spo.extensions import db
from .helpers import utcnow


class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    coupon_type = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=True)
    shop = db.relationship('Shop', backref='coupons')
    program_id = db.Column(db.Integer, db.ForeignKey('bonus_programs.id'), nullable=True)
    program = db.relationship('BonusProgram', backref='coupons')
    value = db.Column(db.Float, nullable=False)
    combinable = db.Column(db.Boolean, nullable=True)
    valid_from = db.Column(db.DateTime, default=utcnow, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, default='active', nullable=False)
    source_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
