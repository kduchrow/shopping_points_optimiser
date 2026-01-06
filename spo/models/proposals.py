from spo.extensions import db

from .helpers import utcnow


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
