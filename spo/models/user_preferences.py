"""User preference models for favorite bonus programs."""

from spo.extensions import db

from .helpers import utcnow


class UserFavoriteProgram(db.Model):
    """User's favorite/preferred bonus programs."""

    __tablename__ = "user_favorite_programs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey("bonus_programs.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # Ensure a user can only favorite a program once
    __table_args__ = (db.UniqueConstraint("user_id", "program_id", name="uq_user_program"),)

    # Relationships
    user = db.relationship("User", backref=db.backref("favorite_programs", lazy=True))
    program = db.relationship("BonusProgram", backref=db.backref("favorited_by", lazy=True))
