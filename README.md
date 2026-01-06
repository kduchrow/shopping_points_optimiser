# 🛍️ Shopping Points Optimiser

Enterprise-ready shopping rewards optimization platform with intelligent shop deduplication, automated scraping, and community-driven rate management.

[![CI Pipeline](https://github.com/kduchrow/shopping_points_optimiser/actions/workflows/ci.yml/badge.svg)](https://github.com/kduchrow/shopping_points_optimiser/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kduchrow/shopping_points_optimiser/branch/main/graph/badge.svg)](https://codecov.io/gh/kduchrow/shopping_points_optimiser)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **Automated Scrapers** - Miles & More, Payback integration
- 🔗 **Smart Shop Deduplication** - AI-powered duplicate detection (98% accuracy)
- 📊 **Rate Management** - Community-driven rate updates with approval workflow
- 🔔 **Notification System** - Real-time notifications for proposals and reviews
- 👥 **User Roles** - Admin, Contributor, User, Viewer
- 🎯 **Modern Admin UI** - Tab-based interface with live progress tracking
- 🐘 **PostgreSQL Database** - Production-ready with Alembic migrations
- 🚀 **CI/CD Pipeline** - Automated testing, linting, and security checks
- 🪝 **Pre-commit Hooks** - Code quality enforcement with ruff, black, isort

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for PostgreSQL)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/kduchrow/shopping_points_optimiser.git
cd shopping_points_optimiser

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL with Docker
docker-compose up -d db

# Run database migrations
python -m alembic upgrade head

# Seed initial data (optional)
python scripts/seed_db.py
```

### Development Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files
```

### Run Application

**Development:**

```bash
python app.py
```

**Production (Docker):**

```bash
docker-compose up
```

Access at: **http://127.0.0.1:5000**

### Default Credentials

| Username    | Password   | Role        |
| ----------- | ---------- | ----------- |
| admin       | admin123   | Admin       |
| contributor | contrib123 | Contributor |
| testuser    | user123    | User        |
| viewer      | viewer123  | Viewer      |

## 📁 Project Structure

```
shopping_points_optimiser/
├── app.py                  # Main Flask application
├── spo/                    # Main application package
│   ├── __init__.py        # Flask app factory
│   ├── version.py         # Version management
│   ├── extensions.py      # Flask extensions
│   ├── models.py          # Database models
│   └── routes/            # Route blueprints
├── migrations/            # Alembic database migrations
├── notifications.py       # Notification system
├── shop_dedup.py         # Shop deduplication logic
├── job_queue.py          # Background job processing
├── requirements.txt      # Python dependencies
├── requirements-dev.txt  # Development dependencies
├── docker-compose.yml    # Docker configuration
├── .pre-commit-config.yaml  # Pre-commit hooks
├── pyproject.toml        # Tool configuration
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
│   ├── base.html       # Base template with navigation & footer
│   ├── admin.html      # Modern admin interface
│   └── ...
│
├── static/             # Static assets
│   ├── css/           # Stylesheets
│   │   ├── main.css   # Main styles + utilities
│   │   ├── admin.css  # Admin-specific styles
│   │   └── result.css # Results page styles
│   └── js/            # JavaScript files
│
├── scripts/            # Utility scripts
│   ├── migrate_sqlite_to_postgres.py  # Migration script
│   └── ...
│
├── tests/             # Test files
│   ├── demo_admin.py
│   ├── test_notifications.py
│   └── ...
│
└── docs/              # Documentation
    ├── CHANGELOG.md
    ├── QUICKSTART.md
    ├── MIGRATION_SQLITE_TO_POSTGRES.md
    ├── PRE_COMMIT_SETUP.md
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

### Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Database Configuration
DATABASE_URL=postgresql+psycopg2://spo:spo@db:5432/spo

# Flask Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False

# Optional
GITHUB_REPO_URL=https://github.com/kduchrow/shopping_points_optimiser
```

### Database

**PostgreSQL** (Production & Development):

- Connection string: `postgresql+psycopg2://spo:spo@db:5432/spo`
- Managed via Alembic migrations
- Auto-migration on Docker container startup

**SQLite** (Legacy, deprecated):

- See [Migration Guide](docs/MIGRATION_SQLITE_TO_POSTGRES.md) for upgrading

### Database Migrations

```bash
# Create new migration
python -m alembic revision --autogenerate -m "Description"

# Apply migrations
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# View migration history
python -m alembic history
```

### Migrate from SQLite to PostgreSQL

```bash
python scripts/migrate_sqlite_to_postgres.py
```

See [detailed migration guide](docs/MIGRATION_SQLITE_TO_POSTGRES.md).

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
# Run all tests with coverage
pytest --cov=spo --cov-report=html

# Run specific test file
pytest tests/test_notifications.py

# Run with verbose output
pytest -v

# Demo scripts
python tests/demo_dedup.py
python tests/demo_admin.py
```

### CI/CD Pipeline

GitHub Actions workflow runs on every push/PR:

1. **Lint & Format** - Ruff code analysis
2. **Type Check** - Pyright static analysis
3. **Tests** - pytest with PostgreSQL service
4. **Alembic Check** - Migration validation
5. **Security** - bandit, safety, detect-secrets

See [CI workflow](.github/workflows/ci.yml) for details.

## 📖 Documentation

- [Changelog](docs/CHANGELOG.md) - Version history and release notes
- [Quick Start Guide](docs/QUICKSTART.md) - Detailed setup instructions
- [Admin System Documentation](docs/ADMIN_SYSTEM.md) - Admin features guide
- [SQLite to PostgreSQL Migration](docs/MIGRATION_SQLITE_TO_POSTGRES.md) - Database migration guide
- [Pre-commit Setup](docs/PRE_COMMIT_SETUP.md) - Code quality automation
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment

## 🛠️ Development

### Code Quality

This project uses automated code quality tools:

- **ruff** - Fast Python linter with auto-fix
- **black** - Code formatter (100 char line-length)
- **isort** - Import sorting
- **pyright** - Type checking
- **prettier** - YAML, JSON, HTML, Markdown formatting
- **yamllint** - YAML validation
- **detect-secrets** - Secret detection

All tools run automatically via pre-commit hooks. See [Pre-commit Setup](docs/PRE_COMMIT_SETUP.md).

### Pre-commit Hooks

```bash
# Install hooks (one-time)
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Update hooks to latest versions
pre-commit autoupdate
```

### Adding a New Scraper

1. Create scraper in `scrapers/your_scraper.py`
2. Inherit from `BaseScraper`
3. Implement `fetch()` method
4. Use `get_or_create_shop_main()` for deduplication
5. Register in admin routes

### Database Migrations

```bash
# After model changes, create migration
python -m alembic revision --autogenerate -m "Add new field"

# Review generated migration in migrations/versions/
# Apply migration
python -m alembic upgrade head
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
3. Install pre-commit hooks (`pre-commit install`)
4. Make changes and commit (`git commit -m 'Add amazing feature'`)
5. Ensure all tests pass (`pytest`)
6. Ensure pre-commit checks pass (`pre-commit run --all-files`)
7. Push to branch (`git push origin feature/amazing`)
8. Open Pull Request

### Code Style

- Python 3.11+ type hints required
- Use modern union syntax: `X | None` instead of `Optional[X]`
- Follow PEP 8 (enforced by ruff/black)
- 100 character line length
- Document public APIs with docstrings

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/kduchrow/shopping_points_optimiser/issues)
- **Changelog**: [docs/CHANGELOG.md](docs/CHANGELOG.md)
- **Version**: See footer in application UI or [spo/version.py](spo/version.py)

## 🎯 Roadmap

- [x] PostgreSQL database with Alembic migrations
- [x] CI/CD pipeline with GitHub Actions
- [x] Pre-commit hooks for code quality
- [x] Version management and changelog
- [ ] Email notifications
- [ ] Advanced analytics dashboard
- [ ] Mobile responsive UI improvements
- [ ] API rate limiting
- [ ] Multi-language support
- [ ] Redis caching layer

## 📋 Versioning

This project follows [Semantic Versioning](https://semver.org/). See [CHANGELOG.md](docs/CHANGELOG.md) for release history.

**Current Version**: See application footer or [spo/version.py](spo/version.py)

---

Made with ❤️ by Shopping Points Optimiser Team
