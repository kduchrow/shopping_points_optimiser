from spo.extensions import db

from .helpers import utcnow


class ScrapeLog(db.Model):
    __tablename__ = "scrape_logs"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=utcnow, nullable=False)
    message = db.Column(db.String, nullable=False)


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
