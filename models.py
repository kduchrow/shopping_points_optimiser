from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class BonusProgram(db.Model):
    __tablename__ = 'bonus_programs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    # value of one point in euros
    point_value_eur = db.Column(db.Float, default=0.0)


# ============ SHOP DEDUPLICATION & NORMALIZATION ============

class ShopMain(db.Model):
    """Canonical shop entry - stable across name/source changes"""
    __tablename__ = 'shop_main'
    id = db.Column(db.String(36), primary_key=True)  # UUID
    canonical_name = db.Column(db.String, nullable=False, index=True)  # Normalized name
    canonical_name_lower = db.Column(db.String, nullable=False, index=True)  # For fuzzy matching
    website = db.Column(db.String, nullable=True)
    logo_url = db.Column(db.String, nullable=True)
    status = db.Column(db.String, default='active', nullable=False)  # active, inactive, merged
    merged_into_id = db.Column(db.String(36), db.ForeignKey('shop_main.id'), nullable=True)  # If merged
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    variants = db.relationship('ShopVariant', backref='main_shop', cascade='all, delete-orphan')


class ShopVariant(db.Model):
    """Source-specific shop entry (linked to ShopMain)"""
    __tablename__ = 'shop_variants'
    id = db.Column(db.Integer, primary_key=True)
    shop_main_id = db.Column(db.String(36), db.ForeignKey('shop_main.id'), nullable=False)
    source = db.Column(db.String, nullable=False)  # 'miles_and_more', 'payback', 'manual', etc.
    source_name = db.Column(db.String, nullable=False)  # Original name from source
    source_id = db.Column(db.String, nullable=True)  # External ID (e.g., partner_id in M&M)
    confidence_score = db.Column(db.Float, default=100.0)  # 0-100, how sure are we of the mapping?
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # For backward compatibility - legacy Shop model compatibility
    db.UniqueConstraint('source', 'source_id', name='unique_source_variant')


class Shop(db.Model):
    """Legacy Shop model - redirects to ShopMain for backward compatibility"""
    __tablename__ = 'shops'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    shop_main_id = db.Column(db.String(36), db.ForeignKey('shop_main.id'), nullable=True)  # Link to canonical
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ShopProgramRate(db.Model):
    __tablename__ = 'shop_program_rates'
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('bonus_programs.id'), nullable=False)
    # how many points are awarded per 1 EUR spent
    points_per_eur = db.Column(db.Float, default=0.0)
    # direct cashback percent (e.g., 2.5 means 2.5% cashback)
    cashback_pct = db.Column(db.Float, default=0.0)
    # validity dates for historical tracking
    valid_from = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=True)  # NULL = currently valid


class ScrapeLog(db.Model):
    __tablename__ = 'scrape_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    message = db.Column(db.String, nullable=False)


# ============ COUPONS & SPECIAL OFFERS ============

class Coupon(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.Integer, primary_key=True)
    # Type: 'multiplier' (z.B. 20fach Punkte) oder 'discount' (z.B. 10% Rabatt)
    coupon_type = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)  # z.B. "20fach Punkte Aktion"
    description = db.Column(db.String, nullable=True)
    
    # Shop (optional, NULL = gilt für alle Shops)
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=True)
    shop = db.relationship('Shop', backref='coupons')
    
    # Programm (optional, NULL = programmunabhängig)
    program_id = db.Column(db.Integer, db.ForeignKey('bonus_programs.id'), nullable=True)
    program = db.relationship('BonusProgram', backref='coupons')
    
    # Wert: bei multiplier = Faktor (z.B. 20), bei discount = Prozent (z.B. 10)
    value = db.Column(db.Float, nullable=False)
    
    # Kombinierbarkeit: True = kann mit anderen kombiniert werden, False = exklusiv, NULL = unbekannt
    combinable = db.Column(db.Boolean, nullable=True)
    
    # Gültigkeit
    valid_from = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    valid_to = db.Column(db.DateTime, nullable=False)
    
    # Status: 'active', 'expired', 'pending' (für Proposals)
    status = db.Column(db.String, default='active', nullable=False)
    
    # Quelle (URL zur Aktion)
    source_url = db.Column(db.String, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


# ============ USER MANAGEMENT ============

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    # Roles: 'viewer', 'user', 'contributor', 'admin'
    role = db.Column(db.String, default='viewer', nullable=False)
    # Status: 'active', 'banned'
    status = db.Column(db.String, default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Flask-Login UserMixin properties
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ContributorRequest(db.Model):
    __tablename__ = 'contributor_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Status: 'pending', 'approved', 'rejected'
    status = db.Column(db.String, default='pending', nullable=False)
    decision_by_admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    decision_at = db.Column(db.DateTime, nullable=True)


# ============ PROPOSAL SYSTEM ============

class Proposal(db.Model):
    __tablename__ = 'proposals'
    id = db.Column(db.Integer, primary_key=True)
    # Type: 'rate_change', 'shop_add', 'program_add', 'coupon_add'
    proposal_type = db.Column(db.String, nullable=False)
    # Status: 'pending', 'approved', 'rejected', 'withdrawn'
    status = db.Column(db.String, default='pending', nullable=False)
    
    # Source: 'user' or 'scraper' - markiert ob von User oder Scraper erstellt
    source = db.Column(db.String, default='user', nullable=False)
    
    # Who created it
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # For rate changes
    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id'), nullable=True)
    program_id = db.Column(db.Integer, db.ForeignKey('bonus_programs.id'), nullable=True)
    proposed_points_per_eur = db.Column(db.Float, nullable=True)
    proposed_cashback_pct = db.Column(db.Float, nullable=True)
    
    # For new shops/programs
    proposed_name = db.Column(db.String, nullable=True)
    proposed_point_value_eur = db.Column(db.Float, nullable=True)
    
    # For coupons
    proposed_coupon_type = db.Column(db.String, nullable=True)  # 'multiplier' or 'discount'
    proposed_coupon_value = db.Column(db.Float, nullable=True)
    proposed_coupon_description = db.Column(db.String, nullable=True)
    proposed_coupon_combinable = db.Column(db.Boolean, nullable=True)
    proposed_coupon_valid_to = db.Column(db.DateTime, nullable=True)
    
    # Description/reason for change
    reason = db.Column(db.String, nullable=True)
    source_url = db.Column(db.String, nullable=True)  # e.g., link to website showing new rate
    
    # When approved
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by_system = db.Column(db.Boolean, default=False)  # True if auto-approved by 3+ votes


class ProposalVote(db.Model):
    __tablename__ = 'proposal_votes'
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    voter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Vote: 1 for upvote, -1 for downvote
    vote = db.Column(db.Integer, nullable=False)
    # Admin votes count as 3x weight, normal votes count as 1x
    vote_weight = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # One contributor can vote once per proposal
    __table_args__ = (db.UniqueConstraint('proposal_id', 'voter_id', name='unique_proposal_voter'),)


class ShopMergeProposal(db.Model):
    """User-proposed shop merges"""
    __tablename__ = 'shop_merge_proposals'
    id = db.Column(db.Integer, primary_key=True)
    variant_a_id = db.Column(db.Integer, db.ForeignKey('shop_variants.id'), nullable=False)
    variant_b_id = db.Column(db.Integer, db.ForeignKey('shop_variants.id'), nullable=False)
    proposed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Status: PENDING, APPROVED, REJECTED
    status = db.Column(db.String, default='PENDING', nullable=False)
    reason = db.Column(db.String, nullable=True)  # Why these should merge
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    decided_at = db.Column(db.DateTime, nullable=True)
    decided_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    decided_reason = db.Column(db.String, nullable=True)


class RateComment(db.Model):
    """Review comments on rates - for feedback/rejection reasons"""
    __tablename__ = 'rate_comments'
    id = db.Column(db.Integer, primary_key=True)
    rate_id = db.Column(db.Integer, db.ForeignKey('shop_program_rates.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_type = db.Column(db.String, nullable=False)  # FEEDBACK, REJECTION_REASON, SUGGESTION
    comment_text = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    rate = db.relationship('ShopProgramRate', backref='comments')
    reviewer = db.relationship('User', backref='rate_comments')


class ProposalAuditTrail(db.Model):
    __tablename__ = 'proposal_audit_trails'
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey('proposals.id'), nullable=False)
    # Action: 'created', 'withdrawn', 'approved', 'rejected', 'vote_added', 'vote_removed'
    action = db.Column(db.String, nullable=False)
    # Who performed the action
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL for system actions
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    details = db.Column(db.String, nullable=True)  # Additional info (e.g., why rejected)


class Notification(db.Model):
    """User notifications for proposals, rate reviews, shop merges, etc."""
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Type: PROPOSAL_REJECTED, PROPOSAL_APPROVED, RATE_COMMENT, MERGE_REJECTED, MERGE_APPROVED
    notification_type = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    message = db.Column(db.String, nullable=False)
    # Link to relevant resource (proposal_id, rate_id, merge_proposal_id, etc.)
    link_type = db.Column(db.String, nullable=True)  # 'proposal', 'rate', 'merge_proposal'
    link_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='notifications')


