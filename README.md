# 🛍️ Shopping Points Optimiser

Find the best bonus programs and cashback for your online shopping.

**Website:** [shopping-optimiser.de](https://shopping-optimiser.de)

[![CI Pipeline](https://github.com/kduchrow/shopping_points_optimiser/actions/workflows/ci.yml/badge.svg)](https://github.com/kduchrow/shopping_points_optimiser/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Core Features

- 🛒 **Shop Matching** - Recognizes 1000+ online retailers
- 💰 **Rate Comparison** - Compares bonus programs (Payback, Miles & More, Shoop, TopCashback, etc.)
- 🤖 **Automated Rates** - Scrapers keep rates fresh
- 👥 **Community Driven** - Users propose and vote on rate updates
- 🌐 **Browser Extension** - Shopping assistant for Chrome/Edge (v1.0.2)
- ⭐ **Favorites** - Save your preferred bonus programs
- 🔐 **User Accounts** - Track proposals and rate history

## 🚀 Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/kduchrow/shopping_points_optimiser.git
cd shopping_points_optimiser

# Create virtual environment & install
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Copy environment
cp .env.example .env

# Start services
docker-compose up -d
python app.py
```

Access at: **http://localhost:5000**

### Browser Extension

Install from [browser_extension/](browser_extension/README.md) directory (Chrome/Edge).

## 📖 Documentation

- **[QUICKSTART](docs/QUICKSTART.md)** - Setup & first steps
- **[DEPLOYMENT](docs/DEPLOYMENT.md)** - Production deployment
- **[CHANGELOG](docs/CHANGELOG.md)** - Version history
- **[Browser Extension](browser_extension/README.md)** - Extension guide

## 🏗️ Architecture

| Component             | Purpose                                       |
| --------------------- | --------------------------------------------- |
| **Flask API**         | Web application & REST endpoints              |
| **PostgreSQL**        | Primary data store with migrations (Alembic)  |
| **Scrapers**          | Automated bonus program rate collection       |
| **Background Jobs**   | Queue processing for scrapers & notifications |
| **Browser Extension** | Client-side shop recognition & rate lookup    |

## 👨‍💻 Development

```bash
# Install dev tools
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Format code
black .
ruff check --fix .
```

## 📝 License

MIT – See [LICENSE](LICENSE) for details.

---

**For questions or feedback:** [shopping-optimiser.de](https://shopping-optimiser.de)

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

## 🚀 Production CI/CD & Deployment (2026 Update)

### Automated CI/CD Pipeline

- **GitHub Actions**: Automated build, test, and deployment pipeline.
- **Build & Push**: Docker image is built and pushed to GitHub Container Registry (GHCR) on every push to `main` or `ci/deployment`.
- **Deploy Job**: Uses SCP and SSH to deploy to your production server.

### Production Deployment

- **docker-compose.prod.override.yml**: Used for production deployments. Integrates Traefik v3 as a reverse proxy, Gunicorn for WSGI, and all configuration via environment variables.
- **Traefik v3**: Handles HTTPS (Let's Encrypt), domain routing, and secure entrypoints. Configurable via `.env` and GitHub secrets.
- **Gunicorn Workers**: Number of workers is configurable via environment variable (`GUNICORN_WORKERS`).
- **.env Generation**: The deploy workflow creates a `.env` file on the server from GitHub repository variables and secrets, ensuring all sensitive data is never committed.
- **Custom SSH Port**: Deployment supports custom SSH ports via the `SSH_PORT` variable. Ensure your firewall/security group allows access from GitHub Actions runners.

### Deployment File Compliance

- All deployment and override files are fully yamllint and pre-commit compliant (no comments, no deprecated fields).

### Retrying Deployment

- **Manual Dispatch**: Go to GitHub → Actions → CI/CD Shopping Points Optimiser → Run workflow (top right) to manually trigger a deployment.
- **Branch Push**: Pushing to `main` or `ci/deployment` will also trigger the workflow.

See `.github/workflows/deploy.yml` and `docker-compose.prod.override.yml` for implementation details.

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

### ✅ Completed

- [x] PostgreSQL database with Alembic migrations
- [x] CI/CD pipeline with GitHub Actions
- [x] Pre-commit hooks for code quality
- [x] Version management and changelog
- [x] Docker-based development and deployment
- [x] Shop deduplication with fuzzy matching
- [x] Merge proposals and community approval workflow
- [x] Admin rescore functionality for shop variants
- [x] Container-only test execution
- [x] Browser Extension with shop recognition (v1.0.2)
- [x] Favorites feature for users
- [x] URL proposal approval workflow
- [x] User authentication & role-based access
- [x] Rate history and deduplication

### 🔄 In Progress

- [ ] Email notifications
- [ ] Advanced analytics dashboard

### 📋 Feature Backlog

#### 🤖 Scrapers & Integrations (High Priority)

**Cashback-Plattformen (🔴 CRITICAL):**

- [x] **Payback Scraper** - Deutsche Cashback-Plattform
- [x] **Miles & More Scraper** - Lufthansa Miles Program
- [x] **Shoop Scraper** - Deutsche Cashback-Plattform
- [x] **TopCashback Scraper** - Europäische Plattform
- [ ] **iGraal Scraper** (M) - Französische Alternative, deutsche Nutzer
- [ ] **Cashback-Vergleich pro Shop** (L) - Eine Shop-Seite zeigt alle Cashback-Wege
- [ ] **Automatischer Cashback-Rate-Update** (S) - Tägliche/wöchentliche Syncs

#### 🎟️ Coupon-Features (High Priority)

- [ ] **Coupon Up/Downvoting** - Community kann Coupons bewerten
- [ ] Coupon-Ablaufdatum automatisch tracken
- [ ] Automatische Deaktivierung abgelaufener Coupons
- [ ] Coupon-Kategorien (Prozent, Festbetrag, Gratis-Versand)
- [ ] User-Kommentare zu Coupons
- [ ] "Coupon erfolgreich genutzt" Feedback-System

#### 📊 Daten-Qualität & Analytics

**Rate Management:**

- [ ] Rate-History: Verlauf von Bonus-Änderungen über Zeit
- [ ] Benachrichtigungen bei Rate-Änderungen für Favoriten-Shops
- [ ] Trend-Analysen: Welche Shops verbessern/verschlechtern sich
- [ ] Saisonale Analysen (z.B. Black Friday Bonus-Spitzen)
- [ ] Best-Rate-Alert: Benachrichtigung bei besonders guten Rates

**Shop-Verwaltung:**

- [ ] Automatische Shop-URL-Verifizierung
- [ ] Shop-Logo automatisch von Clearbit/Brandfetch holen
- [ ] Duplicate-Shop-Detection verbessern (z.B. amazon.de vs amazon.com)
- [ ] Shop-Kategorien (Fashion, Elektronik, Lebensmittel, etc.)

#### 🎨 User Experience

**Navigation & Filter:**

- [ ] Erweiterte Filter auf Index-Seite (Kategorie, Min-Rate, etc.)
- [ ] Sortierung: Beste Rate, Neueste, Alphabetisch
- [ ] Volltextsuche über Shop-Namen
- [ ] Favoriten-Shops speichern und highlighten
- [ ] Kürzlich angesehen / Verlauf

**Personalisierung:**

- [ ] Personalisierte Empfehlungen basierend auf genutzten Programmen
- [ ] "Meine Programme" Profile (Nutzer wählt aktive Programme aus)
- [ ] Benachrichtigungen für neue Coupons bei Favoriten
- [ ] Dark Mode

**Export & Sharing:**

- [ ] CSV-Export von Ergebnissen
- [ ] PDF-Report Generator
- [ ] Teilen-Funktion für Shops (Social Share Links)
- [ ] QR-Code für Shop-URLs

#### 🌐 Community & Social

- [ ] Shop-Bewertungen (5-Sterne-System) neben Rates
- [ ] User-Reputation-System (Punkte für erfolgreiche Proposals)
- [ ] Badges für aktive Contributors
- [ ] Top-Contributors Leaderboard
- [ ] Newsletter für neue Rates/Coupons (opt-in)
- [ ] User-Profil: Persönliche Einsparungen tracking

#### 📱 Mobile & Accessibility

- [ ] Progressive Web App (PWA) Support
- [ ] Browser-Extension (Chrome/Firefox) für schnellen Zugriff
- [ ] Mobile-optimierte UI
- [ ] Barrierefreiheit (WCAG 2.1 AA)

#### 🔧 Technical Improvements

**API & Integration:**

- [ ] GraphQL API zusätzlich zu REST
- [ ] Webhook-System für externe Integrationen
- [ ] Rate-Limiting für API
- [ ] API-Dokumentation mit OpenAPI/Swagger

**Performance:**

- [ ] Redis caching layer
- [ ] Database query optimization
- [ ] CDN für statische Assets
- [ ] Lazy-loading für Shop-Listen

**Internationalization:**

- [ ] Multi-Language Support (EN, FR)
- [ ] Währungs-Konvertierung (EUR, CHF, USD)
- [ ] Lokalisierte Shop-Datenbanken

**Testing & Quality:**

- [ ] E2E-Tests mit Playwright
- [ ] Load testing
- [ ] Mutation testing
- [ ] Automated accessibility testing

#### 🔐 Security & Compliance

- [ ] 2FA (Two-Factor Authentication)
- [ ] GDPR compliance tools (Datenexport, Löschung)
- [ ] Security audit log
- [ ] Content Security Policy (CSP)

#### 📈 Business Features

- [ ] Affiliate-Link-Integration (z.B. AWIN)
- [ ] Partner-Shops hervorheben
- [ ] Sponsored Coupons
- [ ] Admin-Dashboard mit KPIs (User-Growth, Active Shops, etc.)

---

**Prioritäten:**

- 🔴 CRITICAL: Cashback Scrapers (Shoop, TopCashback, iGraal) + Cashback-Vergleich
- 🔴 High: Shop-eigene Bonusprogramme, Coupon-Voting, Rate-History
- 🟡 Medium: Favoriten, Filter, Dark Mode, Personalisierte Empfehlungen
- 🟢 Low: GraphQL, Badges, Affiliate-Links, Multi-Language

**Geschätzte Entwicklungszeit pro Feature:**

- S (Small): 1-3 Tage
- M (Medium): 1-2 Wochen
- L (Large): 3-4 Wochen
- XL (Extra Large): 1-2 Monate

## 📋 Versioning

This project follows [Semantic Versioning](https://semver.org/). See [CHANGELOG.md](docs/CHANGELOG.md) for release history.

**Current Version**: See application footer or [spo/version.py](spo/version.py)

---

Made with ❤️ by Shopping Points Optimiser Team
