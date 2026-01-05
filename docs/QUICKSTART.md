# 🎯 Quick Start - Admin System

## Setup & Start

```bash
# 1. Database Setup
python reset_db.py

# 2. Start Flask Server
python app.py

# 3. Open Admin Panel
# Browser: http://127.0.0.1:5000/admin
# Login: admin / admin123
```

## Demo Scripts

```bash
# Shop Deduplication Demo
python demo_dedup.py

# Notification System Test
python test_notifications.py

# Complete Admin Demo (opens browser)
python demo_admin.py
```

## 🎨 UI Features

### Tab 1: 🤖 Scrapers
- Run Miles & More Scraper
- Run Payback Scraper
- Live progress tracking
- Real-time message feed

### Tab 2: 🔗 Shop Merges
- Pending merge proposals
- One-click approve/reject
- Automatic notifications

### Tab 3: ⭐ Rate Review
- Review rates with low confidence
- Add comments (FEEDBACK, REJECTION_REASON, SUGGESTION)
- Status management

### Tab 4: 🔔 Notifications
- All your notifications
- Unread badge in header
- Mark as read / Mark all as read

## 📊 Current Database Status

After `python test_notifications.py`:
- ShopMain: 4 shops
- ShopVariant: 5 variants
- Merge Proposals: 1 pending
- Notifications: 2 unread (for testuser)

## 🔑 Test Accounts

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| admin | admin123 | admin | Full access to admin panel |
| contributor | contrib123 | contributor | Submit proposals |
| testuser | user123 | user | Regular user (has notifications) |
| viewer | viewer123 | viewer | Read-only access |

## 🧪 Testing Workflow

1. **Test Shop Deduplication:**
   ```bash
   python demo_dedup.py
   # Shows: Amazon + amazon → auto-merged
   ```

2. **Test Notifications:**
   ```bash
   python test_notifications.py
   # Creates test notifications for testuser
   ```

3. **Test Admin UI:**
   - Start server: `python app.py`
   - Login as admin
   - Check Notifications tab
   - Try Shop Merge approval
   - Run a scraper

## 📝 API Endpoints

### Notifications
- `GET /api/notifications` - All notifications
- `GET /api/notifications/unread_count` - Unread count
- `POST /api/notifications/<id>/read` - Mark as read
- `POST /api/notifications/read_all` - Mark all as read

### Shop Merges
- `GET /admin/shops/merge_proposals` - List proposals
- `POST /admin/shops/merge_proposal` - Create proposal
- `POST /admin/shops/merge_proposal/<id>/approve` - Approve
- `POST /admin/shops/merge_proposal/<id>/reject` - Reject

### Rate Review
- `POST /admin/rate/<id>/comment` - Add comment
- `GET /admin/rate/<id>/comments` - Get comments

## 🚀 Next Steps

1. Run scrapers to populate database
2. Check Shop Merges for duplicates
3. Review notifications system
4. Test rate commenting

## 📖 Full Documentation

See [ADMIN_SYSTEM.md](ADMIN_SYSTEM.md) for complete documentation.
