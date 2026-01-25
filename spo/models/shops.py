from spo.extensions import db

from .helpers import utcnow


class ShopMain(db.Model):
    __tablename__ = "shop_main"
    id = db.Column(db.String(36), primary_key=True)
    canonical_name = db.Column(db.String, nullable=False, index=True)
    canonical_name_lower = db.Column(db.String, nullable=False, index=True)
    website = db.Column(db.String, nullable=True)
    logo_url = db.Column(db.String, nullable=True)
    status = db.Column(db.String, default="active", nullable=False)
    merged_into_id = db.Column(db.String(36), db.ForeignKey("shop_main.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    variants = db.relationship("ShopVariant", backref="main_shop", cascade="all, delete-orphan")


class ShopVariant(db.Model):
    __tablename__ = "shop_variants"
    id = db.Column(db.Integer, primary_key=True)
    shop_main_id = db.Column(db.String(36), db.ForeignKey("shop_main.id"), nullable=False)
    source = db.Column(db.String, nullable=False)
    source_name = db.Column(db.String, nullable=False)
    source_id = db.Column(db.String, nullable=True)
    confidence_score = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("shop_main_id", "source", "source_id", name="unique_shop_variant"),
    )


class Shop(db.Model):
    __tablename__ = "shops"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    shop_main_id = db.Column(db.String(36), db.ForeignKey("shop_main.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class ShopProgramRate(db.Model):
    __tablename__ = "shop_program_rates"
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey("bonus_programs.id"), nullable=False)
    points_per_eur = db.Column(db.Float, default=None)  # points earned per 1 EUR spent
    points_absolute = db.Column(db.Float, default=None)  # absolute points earned per transaction
    cashback_pct = db.Column(db.Float, default=None)  # cashback percentage
    cashback_absolute = db.Column(db.Float, default=None)  # absolute cashback amount in EUR
    rate_note = db.Column(db.String, nullable=True)  # Additional notes about the rate
    rate_type = db.Column(db.String, default="shop", nullable=False)  # 'shop' or 'contract'
    # Normalized category reference (nullable)
    category_id = db.Column(db.Integer, db.ForeignKey("shop_categories.id"), nullable=True)
    category_obj = db.relationship("ShopCategory", backref="rates")
    valid_from = db.Column(db.DateTime, default=utcnow, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=True)


class ShopCategory(db.Model):
    __tablename__ = "shop_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("shop_categories.id"), nullable=True)
    parent = db.relationship("ShopCategory", remote_side=[id], backref="children")
