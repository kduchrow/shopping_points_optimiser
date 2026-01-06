from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from spo.extensions import db

from .helpers import utcnow


class BonusProgram(db.Model):
    __tablename__ = "bonus_programs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    point_value_eur = db.Column(db.Float, default=0.0)


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
