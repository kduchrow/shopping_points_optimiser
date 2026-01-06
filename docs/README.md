# 📚 Shopping Points Optimiser - Documentation

Welcome to the complete documentation for Shopping Points Optimiser!

## 🚀 Getting Started

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for new users
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## 🔧 Setup & Configuration

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for new users
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[MIGRATION_SQLITE_TO_POSTGRES.md](MIGRATION_SQLITE_TO_POSTGRES.md)** - Migrate from SQLite to PostgreSQL
- **[PRE_COMMIT_SETUP.md](PRE_COMMIT_SETUP.md)** - Set up code quality automation
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - GitHub repository configuration

## 👨‍💻 Development Workflow

- **[FEATURE_DEVELOPMENT_WORKFLOW.md](FEATURE_DEVELOPMENT_WORKFLOW.md)** - ⭐ Mandatory workflow for implementing new features
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Feature implementation status

## 👨‍💼 Administration

- **[ADMIN_SYSTEM.md](ADMIN_SYSTEM.md)** - Admin panel features and workflows
- **[JOB_QUEUE_README.md](JOB_QUEUE_README.md)** - Background job system

## 🤖 Scraper Documentation

- **[MILES_AND_MORE_USER_GUIDE.md](MILES_AND_MORE_USER_GUIDE.md)** - User guide for Miles & More scraper
- **[MILES_AND_MORE_SCRAPER_IMPLEMENTATION.md](MILES_AND_MORE_SCRAPER_IMPLEMENTATION.md)** - Implementation details
- **[MILES_AND_MORE_TECHNICAL_REFERENCE.md](MILES_AND_MORE_TECHNICAL_REFERENCE.md)** - Technical reference
- **[README_MILES_AND_MORE_INDEX.md](README_MILES_AND_MORE_INDEX.md)** - Miles & More documentation index

## 📋 Release Management

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Feature implementation status
- **[WORKFLOW_DIAGRAM.md](WORKFLOW_DIAGRAM.md)** - System workflow diagrams

## ✅ Checklists

- **[PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)** - Pre-production deployment checklist
- **[FINAL_VERIFICATION_CHECKLIST.md](FINAL_VERIFICATION_CHECKLIST.md)** - Final verification steps

## 🏗️ Architecture & Development

### Technology Stack

- **Backend**: Flask 3.0, SQLAlchemy, Alembic
- **Database**: PostgreSQL 16-Alpine (production), SQLite (legacy)
- **Frontend**: Jinja2 templates, vanilla JavaScript, CSS3
- **Automation**: Playwright for web scraping
- **DevOps**: Docker, Docker Compose, GitHub Actions CI/CD
- **Code Quality**: ruff, black, isort, pyright, pre-commit

### Key Features

#### Smart Shop Deduplication
- **≥98% similarity** → Automatic merge
- **70-98% similarity** → Community review required
- **<70% similarity** → Separate shops
- UUID-based canonical shop identification
- Source tracking (Miles & More, Payback, Manual)

#### Community System
- Role-based access control (Admin, Contributor, User, Viewer)
- Proposal workflow with voting
- Real-time notifications
- Comment system for rate reviews

#### Database Migrations
- Alembic for schema versioning
- Automatic migrations on container startup
- Migration scripts for SQLite → PostgreSQL

#### CI/CD Pipeline
- **Lint & Format**: ruff, black, isort
- **Type Check**: pyright
- **Tests**: pytest with PostgreSQL service
- **Alembic Check**: migration validation
- **Security**: bandit, safety, detect-secrets

## 📝 Quick Reference

### Environment Setup

```bash
# Clone repository
git clone https://github.com/kduchrow/shopping_points_optimiser.git
cd shopping_points_optimiser

# Set up environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start database
docker-compose up -d db

# Run migrations
python -m alembic upgrade head
```

### Docker Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose up --build
```

### Database Commands

```bash
# Create new migration
python -m alembic revision --autogenerate -m "Description"

# Apply migrations
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# View migration history
python -m alembic history

# Migrate from SQLite
python scripts/migrate_sqlite_to_postgres.py
```

### Development Commands

```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Run tests with coverage
pytest --cov=spo --cov-report=html

# Run specific test
pytest tests/test_notifications.py

# Type checking
pyright

# Security scan
bandit -r spo/
safety check
```

## 🔗 External Links

- **GitHub Repository**: https://github.com/kduchrow/shopping_points_optimiser
- **Issue Tracker**: https://github.com/kduchrow/shopping_points_optimiser/issues
- **CI/CD Pipeline**: https://github.com/kduchrow/shopping_points_optimiser/actions

## 📞 Support

For questions or issues:
1. Check this documentation
2. Search [existing issues](https://github.com/kduchrow/shopping_points_optimiser/issues)
3. Create a new issue with detailed information

## 🤝 Contributing

See the [main README](../README.md#contributing) for contribution guidelines.

---

**Version**: See [CHANGELOG.md](CHANGELOG.md) for current version and release history.
