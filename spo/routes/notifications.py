from flask import jsonify
from flask_login import current_user, login_required

from spo.models import Notification
from spo.services import notifications as notification_service


def register_notifications(app):
    @app.route("/api/notifications", methods=["GET"])
    @login_required
    def get_notifications():
        notifications = (
            Notification.query.filter_by(user_id=current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(50)
            .all()
        )

        return jsonify(
            {
                "notifications": [
                    {
                        "id": notification.id,
                        "type": notification.notification_type,
                        "title": notification.title,
                        "message": notification.message,
                        "link_type": notification.link_type,
                        "link_id": notification.link_id,
                        "is_read": notification.is_read,
                        "created_at": notification.created_at.isoformat(),
                    }
                    for notification in notifications
                ],
                "unread_count": Notification.query.filter_by(
                    user_id=current_user.id, is_read=False
                ).count(),
            }
        )

    @app.route("/api/notifications/<int:notification_id>/read", methods=["POST"])
    @login_required
    def mark_notification_read(notification_id):
        if notification_service.mark_as_read(notification_id, current_user.id):
            return jsonify({"success": True})
        return jsonify({"error": "Notification not found"}), 404

    @app.route("/api/notifications/read_all", methods=["POST"])
    @login_required
    def mark_all_notifications_read():
        notification_service.mark_all_as_read(current_user.id)
        return jsonify({"success": True})

    return app
