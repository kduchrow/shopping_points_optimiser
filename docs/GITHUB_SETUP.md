# GitHub & Open Source Anleitung

## 🤔 Solltest du das Projekt auf GitHub hochladen?

### ✅ JA, auf jeden Fall! Gründe:

1. **Version Control** - Änderungen nachverfolgbar, einfach rollback
2. **Backup** - Dein Code ist cloud-gesichert
3. **Zusammenarbeit** - Andere können Issues/PRs erstellen
4. **Portfolio** - Zeigt deine Fähigkeiten als Entwickler
5. **Community** - Open Source kann anderen helfen
6. **CI/CD** - GitHub Actions für automatische Tests/Deployments

### ⚠️ Sicherheit beachten!

**NIEMALS auf GitHub pushen:**
- `.env` Datei (nur `.env.example`!)
- Secrets, API Keys, Passwörter
- Private Daten
- Database Files
- Logs mit sensiblen Infos

✅ **ALWAYS im .gitignore:** Alle sensitive Dateien sind bereits eingetragen!

---

## 🚀 GitHub Setup - Schritt für Schritt

### Schritt 1: GitHub Repository erstellen

1. Gehe zu https://github.com/new
2. Repository Name: `shopping-points-optimiser`
3. Beschreibung: "Optimize your shopping bonus points with intelligent shop deduplication and admin tools"
4. **WICHTIG: Wähle Lizenz**
   - Empfohlen: **MIT License** (flexibel, schon in deinem Projekt)
5. `.gitignore`: Python (wird automatisch verwendet)
6. Create Repository

### Schritt 2: Lokales Git Setup

```bash
cd c:\Git\shopping_points_optimiser

# Git initialisieren (falls nicht schon getan)
git init

# Remote hinzufügen
git remote add origin https://github.com/YOUR-USERNAME/shopping-points-optimiser.git

# Branch umbennen zu 'main' (GitHub Standard)
git branch -M main

# Alle Dateien stagen (ignoriert .gitignore Einträge automatisch)
git add .

# Initial commit
git commit -m "Initial commit: Complete shopping points optimizer with admin system, notifications, and Docker support"

# Zum Remote pushen
git push -u origin main
```

### Schritt 3: Branch Schutz aktivieren (Optional, aber empfohlen)

1. GitHub Repo → Settings → Branches
2. "Add rule" → Branch name pattern: `main`
3. Aktivieren:
   - ✅ Require a pull request before merging
   - ✅ Dismiss stale pull request approvals
   - ✅ Require status checks to pass

---

## 📝 README.md für GitHub optimieren

Dein jetziges README ist gut! Optional: GitHub spezifische Badges hinzufügen

```markdown
# Shopping Points Optimiser

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Flask 3.0+](https://img.shields.io/badge/Flask-3.0+-green)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)

Intelligente Shop-Deduplication für Bonus-Programme mit Admin Dashboard und Notification System.

## Features
- 🏪 Shop Deduplication mit Fuzzy Matching
- 👨‍💼 Modernes Admin Dashboard mit Tabs
- 🔔 Notification System
- ✅ Approval Workflow für Shop Merges
- 📊 Rate Review mit Feedback System
- 🐳 Docker Ready für UNRAID Hosting
- 🗄️ SQLite Database (PostgreSQL ready)

## Quick Start
...rest of your README
```

---

## 🔄 Workflow für zukünftige Änderungen

### Feature entwickeln
```bash
# Feature Branch erstellen
git checkout -b feature/neue-funktion

# Änderungen machen, testen
git add .
git commit -m "feat: Neue Funktion hinzugefügt"

# Zu GitHub pushen
git push origin feature/neue-funktion

# Pull Request erstellen auf GitHub UI
```

### Bug Fix
```bash
git checkout -b fix/bug-name
# ... ändern ...
git commit -m "fix: Wichtigen Bug behoben"
git push origin fix/bug-name
```

### Hauptversion mergen
```bash
# Nach Pull Request Review auf GitHub -> Merge
# Oder lokal:
git checkout main
git pull origin main
git merge feature/neue-funktion
git push origin main
```

---

## 📦 Release Management

### Semantic Versioning verwenden: MAJOR.MINOR.PATCH
- `1.0.0` - Initial Release
- `1.1.0` - New Features
- `1.0.1` - Bug Fixes

### Release erstellen
```bash
# Tag erstellen
git tag -a v1.0.0 -m "Initial release with admin system and notifications"

# Zu GitHub pushen
git push origin v1.0.0
```

Dann auf GitHub: Releases → Draft new release → Tag auswählen → Publish

---

## 🐍 GitHub Actions (Optional: Automatisierung)

### Datei: `.github/workflows/tests.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt pytest

    - name: Run tests
      run: pytest tests/
```

### Datei: `.github/workflows/docker.yml`

```yaml
name: Build Docker Image

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Build Docker image
      run: docker build -t shopping-points-optimiser:latest .
```

---

## 👥 Open Source Best Practices

### CONTRIBUTING.md erstellen

```markdown
# Contributing to Shopping Points Optimiser

## Getting Started

1. Fork das Repository
2. Clone deinen Fork: `git clone https://github.com/YOUR-USERNAME/shopping-points-optimiser.git`
3. Create feature branch: `git checkout -b feature/amazing-feature`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open Pull Request

## Code Style
- Python: PEP 8 via Black formatter
- 4 spaces Einrückung
- Docstrings für alle Functions

## Testing
```bash
pytest tests/
```

## Questions?
Öffne ein Issue oder Discussion!
```

### CODE_OF_CONDUCT.md (Optional aber gut)
- Zeigt Respekt für Contributors
- Template: https://www.contributor-covenant.org/

---

## 🔐 Sicherheits-Checklist für GitHub

- ✅ `.env` ist in `.gitignore`
- ✅ Keine hardcodierten Secrets in Code
- ✅ LICENSE Datei vorhanden
- ✅ README mit Setup-Anleitung
- ✅ UNRAID_HOSTING.md für Deployment
- ✅ Sensible Daten in Docker Secrets, nicht in Dockerfile
- ✅ `.env.example` zeigt Format, aber keine echten Werte

### Secrets für GitHub Actions verwalten

Falls du later CI/CD nutzt:

1. Repo Settings → Secrets and variables → Actions
2. "New repository secret" hinzufügen
3. Name: `SECRET_KEY`, Value: `xxxx` (generierter Wert)

```yaml
# In GitHub Actions nutzen:
env:
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
```

---

## 📊 Optional: GitHub Pages Dokumentation

Wenn du Doku hosten möchtest (auf docs/ basierend):

```bash
# Settings → Pages
# Source: Deploy from a branch
# Branch: main
# Folder: /docs
```

Dann deine Markdown Dateien unter `docs/` werden zu Website!

---

## 🎯 Nächste Schritte

1. ✅ GitHub Account (falls noch nicht)
2. ✅ Repository erstellen
3. ✅ Lokales Git setup
4. ✅ Initial push
5. ✅ Branch Protection (optional)
6. ✅ GitHub Actions Workflows (optional)

---

## 💡 Pro Tipps

### Git Aliases (in deine `.gitconfig`)
```bash
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status
```

### Automated Releases mit Release Drafter
```yaml
# .github/workflows/release-drafter.yml
name: Release Drafter

on:
  push:
    branches:
      - main

jobs:
  update_release_draft:
    runs-on: ubuntu-latest
    steps:
      - uses: release-drafter/release-drafter@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Branch Naming Convention
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation
- `refactor/*` - Code refactoring
- `test/*` - Tests

Beispiel: `git checkout -b feature/email-notifications`

---

## 📚 Weitere Ressourcen

- [GitHub Docs](https://docs.github.com/)
- [Git Basics](https://git-scm.com/book/en/v2)
- [Semantic Versioning](https://semver.org/)
- [Open Source Licenses](https://choosealicense.com/)
- [GitHub Community](https://github.community/)
