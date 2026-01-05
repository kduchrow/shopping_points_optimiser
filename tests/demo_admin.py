"""
Complete System Demo - Admin UI + Notifications
"""

import webbrowser
import time
from app import app, db
from models import User, Notification
from notifications import get_unread_count

def demo():
    print("\n" + "="*70)
    print("🎉 SHOPPING POINTS OPTIMISER - ADMIN SYSTEM DEMO")
    print("="*70 + "\n")
    
    with app.app_context():
        # Show database status
        print("📊 Database Status:")
        from models import ShopMain, ShopVariant, ShopMergeProposal, Notification
        print(f"   ShopMain: {ShopMain.query.count()}")
        print(f"   ShopVariant: {ShopVariant.query.count()}")
        print(f"   Merge Proposals: {ShopMergeProposal.query.count()}")
        print(f"   Notifications: {Notification.query.count()}")
        print()
        
        # Show test users
        print("👥 Test Users:")
        users = User.query.all()
        for u in users:
            unread = get_unread_count(u.id)
            badge = f" ({unread} unread)" if unread > 0 else ""
            print(f"   {u.username:15} - {u.role:12} - {u.email}{badge}")
        print()
        
        # Show notifications for testuser
        testuser = User.query.filter_by(username='testuser').first()
        if testuser:
            notifications = Notification.query.filter_by(user_id=testuser.id).order_by(Notification.created_at.desc()).all()
            if notifications:
                print(f"🔔 Notifications for {testuser.username}:")
                for n in notifications[:3]:  # Show first 3
                    status = "🔴" if not n.is_read else "✅"
                    print(f"   {status} {n.title}")
                    print(f"      {n.message[:60]}...")
                print()
    
    print("="*70)
    print("🌐 ADMIN PANEL")
    print("="*70)
    print()
    print("✅ System is ready!")
    print()
    print("🔑 Login Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("🎯 Features to try:")
    print("   1. 🤖 Scrapers Tab - Run Miles & More scraper")
    print("   2. 🔗 Shop Merges Tab - Review merge proposals")
    print("   3. 🔔 Notifications Tab - See your notifications")
    print("   4. ⭐ Rate Review Tab - Coming soon...")
    print()
    print("📍 URL: http://127.0.0.1:5000/admin")
    print()
    print("Opening browser in 3 seconds...")
    
    # Wait and open browser
    time.sleep(3)
    try:
        webbrowser.open("http://127.0.0.1:5000/admin")
        print("✅ Browser opened!")
    except:
        print("⚠️  Could not open browser automatically")
        print("   Please open: http://127.0.0.1:5000/admin")
    
    print()
    print("="*70)
    print("💡 TIP: Check the Notifications tab to see the test notifications!")
    print("="*70)
    print()

if __name__ == "__main__":
    demo()
