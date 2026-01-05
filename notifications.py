"""
Notification helper functions
"""

from models import db, Notification
from datetime import datetime


def create_notification(user_id, notification_type, title, message, link_type=None, link_id=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        link_type=link_type,
        link_id=link_id,
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def notify_proposal_rejected(proposal, reason):
    """Send notification when proposal is rejected"""
    create_notification(
        user_id=proposal.user_id,
        notification_type='PROPOSAL_REJECTED',
        title='Proposal Rejected',
        message=f'Your proposal has been rejected. Reason: {reason}',
        link_type='proposal',
        link_id=proposal.id
    )


def notify_proposal_approved(proposal):
    """Send notification when proposal is approved"""
    create_notification(
        user_id=proposal.user_id,
        notification_type='PROPOSAL_APPROVED',
        title='Proposal Approved',
        message='Your proposal has been approved and applied!',
        link_type='proposal',
        link_id=proposal.id
    )


def notify_rate_comment(rate, comment, commenter_username):
    """Send notification when someone comments on a rate"""
    # Find the user who submitted the rate (if from proposal)
    from models import Proposal
    proposal = Proposal.query.filter_by(
        shop_id=rate.shop_id,
        program_id=rate.program_id,
        status='approved'
    ).first()
    
    if proposal:
        create_notification(
            user_id=proposal.user_id,
            notification_type='RATE_COMMENT',
            title='New Comment on Your Rate',
            message=f'{commenter_username} commented: {comment.comment_text[:100]}...',
            link_type='rate',
            link_id=rate.id
        )


def notify_merge_rejected(merge_proposal, reason):
    """Send notification when merge proposal is rejected"""
    create_notification(
        user_id=merge_proposal.proposed_by_user_id,
        notification_type='MERGE_REJECTED',
        title='Shop Merge Rejected',
        message=f'Your shop merge proposal was rejected. Reason: {reason}',
        link_type='merge_proposal',
        link_id=merge_proposal.id
    )


def notify_merge_approved(merge_proposal):
    """Send notification when merge proposal is approved"""
    create_notification(
        user_id=merge_proposal.proposed_by_user_id,
        notification_type='MERGE_APPROVED',
        title='Shop Merge Approved',
        message='Your shop merge proposal has been approved and executed!',
        link_type='merge_proposal',
        link_id=merge_proposal.id
    )


def get_unread_count(user_id):
    """Get count of unread notifications for a user"""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_as_read(notification_id, user_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_as_read(user_id):
    """Mark all notifications as read for a user"""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
