# Changelog

All notable changes to Shopping Points Optimiser will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.3] - 2026-01-08

### Added
- `category` column to `ShopProgramRate` table for category-aware rates (migration v0_2_3)
- Category now shown in admin UI for each rate

### Changed
- Version bump to 0.2.3 in all relevant files (see versioning workflow)

### Migration
- Run: `python -m alembic upgrade head` to apply the new column

---

## [0.2.0] - 2026-01-06

### 🔄 Major Update: SQLAlchemy 2.0 Migration

#### Changed

**Core Infrastructure**
- ⬆️ Migrated all models to SQLAlchemy 2.0 syntax
  - Replaced `db.Column()` with `mapped_column()`
  - Added `Mapped[T]` type hints for all columns
  - Modern union types: `X | None` instead of `Optional[X]`
  - Full type safety with Pyright (354 errors → 0)
- 📦 Centralized version management
  - Single source of truth: `spo/version.py`
  - Automatic version sync in `setup.py` and templates
  - Version consistency check script added
- 🗄️ Migration naming aligned with app version (v0_2_0)
- 🐳 Docker image metadata with OCI labels
  - Version, build date, and git commit in image labels
  - Automatic tagging with semantic version
  - Build scripts for PowerShell and Bash

**Developer Experience**
- ✅ Enhanced IDE autocomplete and refactoring support
- ✅ Better type checking and error detection
- ✅ Pre-commit hooks passing (15/15)
- ✅ All tests passing (43/43)

#### Added
- 📝 Version bump checklist in development workflow
- 🔍 `scripts/check_version.py` for version consistency validation
- 📚 Documentation updates for version management

#### Technical Details
- No database schema changes (backward compatible)
- No breaking API changes
- All existing functionality preserved
- PostgreSQL 16 support confirmed

---

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

### Development Infrastructure

#### Added

**Database Migration**
- 🐘 PostgreSQL 16-Alpine support with Docker integration
- 🔄 Alembic migration system with automatic schema versioning
- 📦 SQLite → PostgreSQL migration script with data preservation
- ✅ Automatic migration execution on container startup

**CI/CD Pipeline**
- 🚀 GitHub Actions workflow with 5-stage pipeline
- 🔍 Lint stage: Ruff code analysis
- 📋 Type checking: Pyright static analysis
- 🧪 Test stage: pytest with coverage reporting to Codecov
- 🏗️ Alembic schema validation
- 🔐 Security scanning: bandit, safety, detect-secrets

**Code Quality Automation**
- 🪝 Pre-commit hooks framework (16 hooks)
- 📐 Code formatting: black (100 char line-length), prettier
- 🔧 Import management: isort (black-compatible profile)
- 🧹 Lint: ruff with Python 3.10+ modernization rules (UP007)
- 📄 YAML validation: yamllint
- 🔐 Secret detection: detect-secrets with baseline

**Template & Static Assets**
- 🎨 Unified base.html template with footer showing version + GitHub link
- 📦 CSS extracted to static/css/ folder structure
- 🔗 All templates refactored to extend base.html

**Documentation**
- 📖 Migration guide: MIGRATION_SQLITE_TO_POSTGRES.md
- 🔧 Pre-commit setup: PRE_COMMIT_SETUP.md

#### Changed

- 🔄 Type hints: Upgraded to Python 3.10+ union syntax (Optional[X] → X | None)
- 📋 Docker: Added Postgres health checks and entrypoint migration
- 🔑 Environment: DATABASE_URL now points to PostgreSQL by default

#### Technical Details

**Docker Compose Services**
- `db`: PostgreSQL 16-Alpine with volume persistence
- `shopping-points`: Flask application with auto-migrations

**Database Configuration**
- Connection: `postgresql+psycopg2://spo:spo@db:5432/spo`
- Migrations: Alembic-managed, auto-executed on startup
- Data: Full migration from SQLite with sequence resets and FK ordering

**Versions Locked**
- Python: 3.11+ (required for union type syntax)
- PostgreSQL: 16-Alpine
- Alembic: Latest stable
- Pre-commit: v4.5.0

### Planned Features
- Email notifications
- Advanced analytics dashboard
- Mobile responsive UI
- Multi-language support
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
