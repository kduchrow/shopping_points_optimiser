from datetime import UTC, datetime

from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from spo.extensions import db


def utcnow():
    return datetime.now(UTC)


class BonusProgram(db.Model):
    __tablename__ = "bonus_programs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    point_value_eur: Mapped[float] = mapped_column(default=0.0)


class ShopMain(db.Model):
    __tablename__ = "shop_main"
    id: Mapped[str] = mapped_column(db.String(36), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(index=True)
    canonical_name_lower: Mapped[str] = mapped_column(index=True)
    website: Mapped[str | None] = mapped_column(default=None)
    logo_url: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="active")
    merged_into_id: Mapped[str | None] = mapped_column(
        db.String(36), db.ForeignKey("shop_main.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    updated_by_user_id: Mapped[int | None] = mapped_column(db.ForeignKey("users.id"), default=None)
    variants = db.relationship("ShopVariant", backref="main_shop", cascade="all, delete-orphan")


class ShopVariant(db.Model):
    __tablename__ = "shop_variants"
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_main_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey("shop_main.id"))
    source: Mapped[str]
    source_name: Mapped[str]
    source_id: Mapped[str | None] = mapped_column(default=None)
    confidence_score: Mapped[float] = mapped_column(default=100.0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    db.UniqueConstraint("source", "source_id", name="unique_source_variant")


class Shop(db.Model):
    __tablename__ = "shops"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    shop_main_id: Mapped[str | None] = mapped_column(
        db.String(36), db.ForeignKey("shop_main.id"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class ShopProgramRate(db.Model):
    __tablename__ = "shop_program_rates"
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_id: Mapped[int] = mapped_column(db.ForeignKey("shops.id"))
    program_id: Mapped[int] = mapped_column(db.ForeignKey("bonus_programs.id"))
    points_per_eur: Mapped[float] = mapped_column(default=0.0)
    cashback_pct: Mapped[float] = mapped_column(default=0.0)
    valid_from: Mapped[datetime] = mapped_column(default=utcnow)
    valid_to: Mapped[datetime | None] = mapped_column(default=None)


class ScrapeLog(db.Model):
    __tablename__ = "scrape_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)
    message: Mapped[str]


class Coupon(db.Model):
    __tablename__ = "coupons"
    id: Mapped[int] = mapped_column(primary_key=True)
    coupon_type: Mapped[str]
    name: Mapped[str]
    description: Mapped[str | None] = mapped_column(default=None)
    shop_id: Mapped[int | None] = mapped_column(db.ForeignKey("shops.id"), default=None)
    shop = db.relationship("Shop", backref="coupons")
    program_id: Mapped[int | None] = mapped_column(db.ForeignKey("bonus_programs.id"), default=None)
    program = db.relationship("BonusProgram", backref="coupons")
    value: Mapped[float]
    combinable: Mapped[bool | None] = mapped_column(default=None)
    valid_from: Mapped[datetime] = mapped_column(default=utcnow)
    valid_to: Mapped[datetime]
    status: Mapped[str] = mapped_column(default="active")
    source_url: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    role: Mapped[str] = mapped_column(default="viewer")
    status: Mapped[str] = mapped_column(default="active")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class ContributorRequest(db.Model):
    __tablename__ = "contributor_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    status: Mapped[str] = mapped_column(default="pending")
    decision_by_admin_id: Mapped[int | None] = mapped_column(
        db.ForeignKey("users.id"), default=None
    )
    decision_at: Mapped[datetime | None] = mapped_column(default=None)


class Proposal(db.Model):
    __tablename__ = "proposals"
    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_type: Mapped[str]
    status: Mapped[str] = mapped_column(default="pending")
    source: Mapped[str] = mapped_column(default="user")
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    shop_id: Mapped[int | None] = mapped_column(db.ForeignKey("shops.id"), default=None)
    program_id: Mapped[int | None] = mapped_column(db.ForeignKey("bonus_programs.id"), default=None)
    proposed_points_per_eur: Mapped[float | None] = mapped_column(default=None)
    proposed_cashback_pct: Mapped[float | None] = mapped_column(default=None)
    proposed_name: Mapped[str | None] = mapped_column(default=None)
    proposed_point_value_eur: Mapped[float | None] = mapped_column(default=None)
    proposed_coupon_type: Mapped[str | None] = mapped_column(default=None)
    proposed_coupon_value: Mapped[float | None] = mapped_column(default=None)
    proposed_coupon_description: Mapped[str | None] = mapped_column(default=None)
    proposed_coupon_combinable: Mapped[bool | None] = mapped_column(default=None)
    proposed_coupon_valid_to: Mapped[datetime | None] = mapped_column(default=None)
    reason: Mapped[str | None] = mapped_column(default=None)
    source_url: Mapped[str | None] = mapped_column(default=None)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
    approved_by_system: Mapped[bool] = mapped_column(default=False)


class ProposalVote(db.Model):
    __tablename__ = "proposal_votes"
    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(db.ForeignKey("proposals.id"))
    voter_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    vote: Mapped[int]
    vote_weight: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    __table_args__ = (db.UniqueConstraint("proposal_id", "voter_id", name="unique_proposal_voter"),)


class ShopMergeProposal(db.Model):
    __tablename__ = "shop_merge_proposals"
    id: Mapped[int] = mapped_column(primary_key=True)
    variant_a_id: Mapped[int] = mapped_column(db.ForeignKey("shop_variants.id"))
    variant_b_id: Mapped[int] = mapped_column(db.ForeignKey("shop_variants.id"))
    proposed_by_user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(default="PENDING")
    reason: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(default=None)
    decided_by_user_id: Mapped[int | None] = mapped_column(db.ForeignKey("users.id"), default=None)
    decided_reason: Mapped[str | None] = mapped_column(default=None)


class ShopMetadataProposal(db.Model):
    __tablename__ = "shop_metadata_proposals"
    id: Mapped[int] = mapped_column(primary_key=True)
    shop_main_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey("shop_main.id"))
    proposed_name: Mapped[str | None] = mapped_column(default=None)
    proposed_website: Mapped[str | None] = mapped_column(default=None)
    proposed_logo_url: Mapped[str | None] = mapped_column(default=None)
    reason: Mapped[str | None] = mapped_column(default=None)
    proposed_by_user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(default="PENDING")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(default=None)
    decided_by_user_id: Mapped[int | None] = mapped_column(db.ForeignKey("users.id"), default=None)
    decided_reason: Mapped[str | None] = mapped_column(default=None)


class RateComment(db.Model):
    __tablename__ = "rate_comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    rate_id: Mapped[int] = mapped_column(db.ForeignKey("shop_program_rates.id"))
    reviewer_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    comment_type: Mapped[str]
    comment_text: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    rate = db.relationship("ShopProgramRate", backref="comments")
    reviewer = db.relationship("User", backref="rate_comments")


class ProposalAuditTrail(db.Model):
    __tablename__ = "proposal_audit_trails"
    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(db.ForeignKey("proposals.id"))
    action: Mapped[str]
    actor_id: Mapped[int | None] = mapped_column(db.ForeignKey("users.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    details: Mapped[str | None] = mapped_column(default=None)


class Notification(db.Model):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    notification_type: Mapped[str]
    title: Mapped[str]
    message: Mapped[str]
    link_type: Mapped[str | None] = mapped_column(default=None)
    link_id: Mapped[int | None] = mapped_column(default=None)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    user = db.relationship("User", backref="notifications")
