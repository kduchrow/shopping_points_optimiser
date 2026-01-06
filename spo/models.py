from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from spo.extensions import db


def utcnow():
    return datetime.now(UTC)


class BonusProgram(db.Model):
    __tablename__ = "bonus_programs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    point_value_eur = db.Column(db.Float, default=0.0)


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
    db.UniqueConstraint("source", "source_id", name="unique_source_variant")


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
    points_per_eur = db.Column(db.Float, default=0.0)
    cashback_pct = db.Column(db.Float, default=0.0)
    valid_from = db.Column(db.DateTime, default=utcnow, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=True)


class ScrapeLog(db.Model):
    __tablename__ = "scrape_logs"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False)
    message = db.Column(db.String, nullable=False)


class Coupon(db.Model):
    __tablename__ = "coupons"
    id = db.Column(db.Integer, primary_key=True)
    coupon_type = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True)
    shop = db.relationship("Shop", backref="coupons")
    program_id = db.Column(db.Integer, db.ForeignKey("bonus_programs.id"), nullable=True)
    program = db.relationship("BonusProgram", backref="coupons")
    value = db.Column(db.Float, nullable=False)
    combinable = db.Column(db.Boolean, nullable=True)
    valid_from = db.Column(db.DateTime, default=utcnow, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, default="active", nullable=False)
    source_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default="viewer", nullable=False)
    status = db.Column(db.String, default="active", nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class ContributorRequest(db.Model):
    __tablename__ = "contributor_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    status = db.Column(db.String, default="pending", nullable=False)
    decision_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    decision_at = db.Column(db.DateTime, nullable=True)


class Proposal(db.Model):
    __tablename__ = "proposals"
    id = db.Column(db.Integer, primary_key=True)
    proposal_type = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default="pending", nullable=False)
    source = db.Column(db.String, default="user", nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("shops.id"), nullable=True)
    program_id = db.Column(db.Integer, db.ForeignKey("bonus_programs.id"), nullable=True)
    proposed_points_per_eur = db.Column(db.Float, nullable=True)
    proposed_cashback_pct = db.Column(db.Float, nullable=True)
    proposed_name = db.Column(db.String, nullable=True)
    proposed_point_value_eur = db.Column(db.Float, nullable=True)
    proposed_coupon_type = db.Column(db.String, nullable=True)
    proposed_coupon_value = db.Column(db.Float, nullable=True)
    proposed_coupon_description = db.Column(db.String, nullable=True)
    proposed_coupon_combinable = db.Column(db.Boolean, nullable=True)
    proposed_coupon_valid_to = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String, nullable=True)
    source_url = db.Column(db.String, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by_system = db.Column(db.Boolean, default=False)


class ProposalVote(db.Model):
    __tablename__ = "proposal_votes"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id"), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    vote = db.Column(db.Integer, nullable=False)
    vote_weight = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    __table_args__ = (db.UniqueConstraint("proposal_id", "voter_id", name="unique_proposal_voter"),)


class ShopMergeProposal(db.Model):
    __tablename__ = "shop_merge_proposals"
    id = db.Column(db.Integer, primary_key=True)
    variant_a_id = db.Column(db.Integer, db.ForeignKey("shop_variants.id"), nullable=False)
    variant_b_id = db.Column(db.Integer, db.ForeignKey("shop_variants.id"), nullable=False)
    proposed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String, default="PENDING", nullable=False)
    reason = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    decided_at = db.Column(db.DateTime, nullable=True)
    decided_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    decided_reason = db.Column(db.String, nullable=True)


class ShopMetadataProposal(db.Model):
    __tablename__ = "shop_metadata_proposals"
    id = db.Column(db.Integer, primary_key=True)
    shop_main_id = db.Column(db.String(36), db.ForeignKey("shop_main.id"), nullable=False)
    proposed_name = db.Column(db.String, nullable=True)
    proposed_website = db.Column(db.String, nullable=True)
    proposed_logo_url = db.Column(db.String, nullable=True)
    reason = db.Column(db.String, nullable=True)
    proposed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String, default="PENDING", nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    decided_at = db.Column(db.DateTime, nullable=True)
    decided_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    decided_reason = db.Column(db.String, nullable=True)


class RateComment(db.Model):
    __tablename__ = "rate_comments"
    id = db.Column(db.Integer, primary_key=True)
    rate_id = db.Column(db.Integer, db.ForeignKey("shop_program_rates.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment_type = db.Column(db.String, nullable=False)
    comment_text = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    rate = db.relationship("ShopProgramRate", backref="comments")
    reviewer = db.relationship("User", backref="rate_comments")


class ProposalAuditTrail(db.Model):
    __tablename__ = "proposal_audit_trails"
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("proposals.id"), nullable=False)
    action = db.Column(db.String, nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    details = db.Column(db.String, nullable=True)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    notification_type = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    link_type = db.Column(db.String, nullable=True)
    link_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    user = db.relationship("User", backref="notifications")
