# Changelog

All notable changes to Shopping Points Optimiser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0] - 2026-01-05

### 🎉 Initial Release

#### Added

**Core Features**
- 🤖 Automated web scrapers for Miles & More and Payback
- 📊 Bonus program management system
- 🏪 Shop and rate tracking
- 👥 User authentication with role-based access control (Admin, Contributor, User, Viewer)
- 💾 SQLite database with full history tracking

**Shop Deduplication System**
- Intelligent shop duplicate detection (≥98% accuracy)
- Automatic merging for identical shops
- Community review for ambiguous cases (70-98% similarity)
- UUID-based shop identification
- Source tracking (Miles & More, Payback, Manual)

**Admin Panel**
- Modern tab-based UI
- Real-time scraper progress tracking
- Shop merge approval workflow
- Rate review system with comments
- Notification management

**Notification System**
- Real-time user notifications
- Unread badge in header
- 5 notification types (Proposal Approved/Rejected, Rate Comment, Merge Approved/Rejected)
- Mark as read functionality
- Auto-refresh every 30 seconds

**Background Job Queue**
- Non-blocking scraper execution
- Live progress tracking
- Job status monitoring
- Message feed with timestamps

**API Endpoints**
- RESTful API for all major features
- Notification management endpoints
- Shop merge proposal endpoints
- Rate comment endpoints
- Job status endpoints

**Developer Tools**
- Comprehensive test suite
- Demo scripts for all major features
- Database reset and seeding tools
- Documentation and guides

#### Technical Details

**Database Models**
- `User` - User accounts with roles
- `BonusProgram` - Loyalty programs
- `ShopMain` - Canonical shop entries
- `ShopVariant` - Source-specific shop variants
- `Shop` - Legacy shop model (backward compatibility)
- `ShopProgramRate` - Shop rates with history tracking
- `ShopMergeProposal` - Community merge proposals
- `RateComment` - Review comments on rates
- `Notification` - User notifications
- `Proposal` - Rate change proposals
- `ProposalVote` - Community voting
- `Coupon` - Special offers and multipliers
- `ScrapeLog` - Scraper execution logs

**Scrapers**
- Miles & More scraper (Playwright-based)
- Payback scraper (Playwright-based)
- Base scraper class for extensibility
- Automatic shop deduplication
- Fallback rate system

**Security**
- Password hashing (werkzeug)
- CSRF protection (Flask)
- Role-based access control
- Input validation

**Performance**
- Background job processing
- SQLite with proper indexing
- Efficient fuzzy matching algorithm
- Optimized query patterns

#### Documentation
- README.md - Main documentation
- QUICKSTART.md - Quick start guide
- ADMIN_SYSTEM.md - Admin system documentation
- DEPLOYMENT.md - Production deployment guide
- API documentation inline

#### Testing
- Unit tests for shop deduplication
- Integration tests for notifications
- Demo scripts for all features
- Database integrity tests

### Project Structure

```
shopping_points_optimiser/
├── app.py                 # Main application
├── models.py             # Database models
├── notifications.py      # Notification system
├── shop_dedup.py        # Deduplication logic
├── job_queue.py         # Background jobs
├── requirements.txt     # Dependencies
├── .gitignore          # Git ignore rules
├── LICENSE             # MIT License
├── README.md           # Main documentation
│
├── bonus_programs/     # Bonus program implementations
├── scrapers/          # Web scrapers
├── templates/         # HTML templates
├── shops/            # Shop implementations
├── scripts/          # Utility scripts
├── tests/           # Test suite
└── docs/           # Documentation
```

### Dependencies

**Python Packages**
- Flask 3.0.0 - Web framework
- Flask-SQLAlchemy 3.1.1 - Database ORM
- Flask-Login 0.6.3 - User session management
- Playwright 1.40.0 - Browser automation
- Werkzeug 3.0.1 - Security utilities

### Known Issues

None at initial release.

### Migration Notes

This is the initial release. No migration required.

---

## [Unreleased]

### Planned Features
- Email notifications
- Advanced analytics dashboard
- Mobile responsive UI
- Multi-language support
- Docker deployment
- PostgreSQL support
- Redis caching
- API rate limiting
- OAuth integration

---

**Legend:**
- 🎉 Major release
- ✨ New feature
- 🐛 Bug fix
- 🔒 Security fix
- 📝 Documentation
- ⚡ Performance improvement
- 🔧 Configuration change
- 🗑️ Deprecation
