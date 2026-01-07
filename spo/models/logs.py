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


class ScheduledJob(db.Model):
    """Stores configuration for scheduled/cron jobs."""

    __tablename__ = "scheduled_jobs"
    id = db.Column(db.Integer, primary_key=True)
    job_name = db.Column(db.String, unique=True, index=True, nullable=False)
    job_type = db.Column(db.String, nullable=False)
    cron_expression = db.Column(db.String, nullable=False)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    last_run_at = db.Column(db.DateTime, nullable=True)
    last_run_status = db.Column(db.String, nullable=True)
    last_run_message = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
