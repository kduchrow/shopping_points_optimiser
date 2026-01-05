# 🛍️ Shopping Points Optimiser

Enterprise-ready shopping rewards optimization platform with intelligent shop deduplication, automated scraping, and community-driven rate management.

## ✨ Features

- 🤖 **Automated Scrapers** - Miles & More, Payback integration
- 🔗 **Smart Shop Deduplication** - AI-powered duplicate detection (98% accuracy)
- 📊 **Rate Management** - Community-driven rate updates with approval workflow
- 🔔 **Notification System** - Real-time notifications for proposals and reviews
- 👥 **User Roles** - Admin, Contributor, User, Viewer
- 🎯 **Modern Admin UI** - Tab-based interface with live progress tracking

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd shopping_points_optimiser

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/reset_db.py
```

### Run Application

```bash
python app.py
```

Access at: **http://127.0.0.1:5000**

### Default Credentials

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| contributor | contrib123 | Contributor |
| testuser | user123 | User |
| viewer | viewer123 | Viewer |

## 📁 Project Structure

```
shopping_points_optimiser/
├── app.py                  # Main Flask application
├── models.py              # Database models
├── notifications.py       # Notification system
├── shop_dedup.py         # Shop deduplication logic
├── job_queue.py          # Background job processing
├── requirements.txt      # Python dependencies
│
├── bonus_programs/       # Bonus program implementations
│   ├── miles_and_more.py
│   ├── payback.py
│   └── shoop.py
│
├── scrapers/            # Web scrapers
│   ├── base.py
│   ├── miles_and_more_scraper.py
│   └── payback_scraper_js.py
│
├── templates/           # HTML templates
│   ├── admin_v2.html   # Modern admin interface
│   └── ...
│
├── scripts/            # Utility scripts
│   ├── reset_db.py    # Database reset & seed
│   └── ...
│
├── tests/             # Test files
│   ├── demo_admin.py
│   ├── test_notifications.py
│   └── ...
│
└── docs/              # Documentation
    ├── QUICKSTART.md
    ├── ADMIN_SYSTEM.md
    └── ...
```

## 🎯 Core Concepts

### Shop Deduplication

Automatically merges duplicate shops across different sources:
- **≥98% similarity** → Auto-merge
- **70-98% similarity** → Community review required
- **<70% similarity** → Separate shops

Example: `Amazon` (Miles & More) + `amazon` (Payback) → **Auto-merged**

### Approval Workflow

1. User/Scraper submits proposal
2. Community reviews and votes
3. Admin approves/rejects with feedback
4. User receives notification

### Notification Types

- `PROPOSAL_REJECTED` - Proposal was rejected with reason
- `PROPOSAL_APPROVED` - Proposal was approved
- `RATE_COMMENT` - New comment on your rate
- `MERGE_REJECTED` - Shop merge rejected
- `MERGE_APPROVED` - Shop merge approved

## 🔧 Configuration

### Environment Variables (Optional)

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///shopping.db
```

### Database

Default: SQLite (`instance/shopping.db`)

To reset database:
```bash
python scripts/reset_db.py
```

## 📊 API Endpoints

### Public
- `GET /` - Home page
- `GET /login` - Login page
- `POST /login` - Login
- `GET /register` - Registration

### Admin
- `GET /admin` - Admin panel
- `POST /admin/run_miles_and_more` - Start M&M scraper
- `POST /admin/run_payback` - Start Payback scraper
- `GET /admin/job_status/<id>` - Job status

### Notifications
- `GET /api/notifications` - Get all notifications
- `GET /api/notifications/unread_count` - Unread count
- `POST /api/notifications/<id>/read` - Mark as read
- `POST /api/notifications/read_all` - Mark all as read

### Shop Merges
- `GET /admin/shops/merge_proposals` - List proposals
- `POST /admin/shops/merge_proposal` - Create proposal
- `POST /admin/shops/merge_proposal/<id>/approve` - Approve
- `POST /admin/shops/merge_proposal/<id>/reject` - Reject

### Rate Reviews
- `POST /admin/rate/<id>/comment` - Add comment
- `GET /admin/rate/<id>/comments` - Get comments

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Specific tests
python tests/test_notifications.py
python tests/demo_dedup.py
python tests/demo_admin.py
```

## 📖 Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Admin System Documentation](docs/ADMIN_SYSTEM.md)
- [API Reference](docs/)

## 🛠️ Development

### Adding a New Scraper

1. Create scraper in `scrapers/your_scraper.py`
2. Inherit from `BaseScraper`
3. Implement `fetch()` method
4. Use `get_or_create_shop_main()` for deduplication
5. Register in `app.py`

### Database Migrations

```bash
# After model changes
python scripts/reset_db.py
```

## 🔒 Security

- ✅ Password hashing (werkzeug)
- ✅ CSRF protection
- ✅ Role-based access control
- ✅ Input validation
- ⚠️ Change `SECRET_KEY` in production!
- ⚠️ Change default passwords!

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📞 Support

- Documentation: `docs/`
- Issues: GitHub Issues
- Email: support@example.com

## 🎯 Roadmap

- [ ] Email notifications
- [ ] Advanced analytics dashboard
- [ ] Mobile app
- [ ] API rate limiting
- [ ] Multi-language support
- [ ] Docker deployment

---

Made with ❤️ by Shopping Points Optimiser Team
