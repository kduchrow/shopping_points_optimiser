"""
Test notification system
"""

from app import app, db
from models import User, Notification, ShopMergeProposal, ShopVariant
from notifications import (
    create_notification, 
    notify_merge_rejected,
    get_unread_count
)
from shop_dedup import get_or_create_shop_main

def test_notifications():
    with app.app_context():
        print("\n=== Notification System Test ===\n")
        
        # Get test user
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("❌ Test user not found. Run reset_db.py first.")
            return
        
        print(f"👤 Test User: {user.username} (ID: {user.id})\n")
        
        # Test 1: Create basic notification
        print("1️⃣  Creating test notification...")
        notif = create_notification(
            user_id=user.id,
            notification_type='TEST',
            title='Test Notification',
            message='This is a test notification to verify the system works!',
            link_type='proposal',
            link_id=1
        )
        print(f"   ✅ Created notification ID: {notif.id}")
        print(f"   Unread count: {get_unread_count(user.id)}\n")
        
        # Test 2: Create shop merge proposal and reject it (triggers notification)
        print("2️⃣  Creating shop merge proposal...")
        
        # Create two shop variants
        shop1, _, _ = get_or_create_shop_main("Test Shop A", "test", "test1")
        shop2, _, _ = get_or_create_shop_main("Test Shop B", "test", "test2")
        
        variant1 = ShopVariant.query.filter_by(shop_main_id=shop1.id).first()
        variant2 = ShopVariant.query.filter_by(shop_main_id=shop2.id).first()
        
        merge_proposal = ShopMergeProposal(
            variant_a_id=variant1.id,
            variant_b_id=variant2.id,
            proposed_by_user_id=user.id,
            reason="Testing merge proposal rejection notification",
            status='PENDING'
        )
        db.session.add(merge_proposal)
        db.session.commit()
        print(f"   ✅ Created merge proposal ID: {merge_proposal.id}")
        
        # Reject it and trigger notification
        print("   Rejecting proposal...")
        notify_merge_rejected(merge_proposal, "This is a test rejection")
        print(f"   ✅ Notification sent!")
        print(f"   Unread count: {get_unread_count(user.id)}\n")
        
        # Show all notifications
        print("=== All Notifications ===\n")
        notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
        
        for n in notifications:
            status = "🔴 UNREAD" if not n.is_read else "✅ READ"
            print(f"{status} | {n.notification_type}")
            print(f"  Title: {n.title}")
            print(f"  Message: {n.message}")
            print(f"  Created: {n.created_at}")
            print()
        
        print(f"Total notifications: {len(notifications)}")
        print(f"Unread: {get_unread_count(user.id)}")
        
        print("\n✅ Notification system test completed!")
        print("\n💡 Next: Start the Flask app and visit /admin to see the UI")

if __name__ == "__main__":
    test_notifications()
