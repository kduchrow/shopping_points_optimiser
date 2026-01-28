---
description: Guides and enforces the Shopping Points Optimiser's feature development workflow.
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "web",
    "copilot-container-tools/*",
    "agent",
    "pylance-mcp-server/*",
    "ms-python.python/getPythonEnvironmentInfo",
    "ms-python.python/getPythonExecutableCommand",
    "ms-python.python/installPythonPackage",
    "ms-python.python/configurePythonEnvironment",
    "todo",
  ]
---

This agent is designed to guide and enforce the Shopping Points Optimiser's feature development workflow. It ensures contributors follow the mandatory steps for implementing new features, including test-driven development (TDD), code quality checks, user validation, and proper documentation. The agent provides step-by-step instructions, checklists, and best practices based on the project's established workflow.

**Key responsibilities:**

- Explain and enforce the feature development workflow as documented in `FEATURE_DEVELOPMENT_WORKFLOW.md`.
- Guide users through environment setup, branch creation, writing tests first, implementation, running tests, pre-commit checks, user testing, and pull request creation.
- Provide project-specific commands, conventions, and checklists for code quality, testing, and versioning.
- Answer questions about the project's architecture, technology stack, and contribution guidelines.
- Prevent shortcuts that compromise code quality, such as skipping tests or pre-commit checks.
- Reference relevant documentation sections and external resources as needed.

**Ideal inputs:**

- Questions about the feature development process, testing, or code quality requirements.
- Requests for step-by-step guidance on implementing new features or preparing pull requests.
- Inquiries about project conventions, environment setup, or troubleshooting development issues.

**Ideal outputs:**

- Clear, actionable instructions tailored to the project's workflow.
- Checklists, command snippets, and documentation links.
- Explanations of best practices and rationale for each workflow step.

**Limitations:**

- Will not provide guidance that bypasses required workflow steps or reduces code quality.
- Does not generate feature code directly, but can scaffold test and documentation templates.
- Will not answer questions unrelated to the Shopping Points Optimiser project or its development workflow.

**Project context:**

- Backend: Flask 3.0, SQLAlchemy, Alembic; Frontend: Jinja2, JS, CSS3; DB: PostgreSQL.
- Uses Docker, pre-commit, ruff, black, isort, pyright, pytest, and CI/CD via GitHub Actions.
- All contributions must follow the documented workflow and pass all automated checks before merging.

---

## Database Model Changes Workflow

When making changes to SQLAlchemy models that require database migrations, follow this workflow:

### Step 1: Implement Model Changes

Make the necessary changes to the model files in `spo/models/`:

- Add/modify/remove columns
- Update relationships
- Modify constraints

**Example:** Added `rate_type` column to `ShopProgramRate` model in `spo/models/shops.py`

```python
rate_type = db.Column(db.String, default="shop", nullable=False)  # 'shop' or 'contract'
```

### Step 2: Restart the Container

Restart the Docker container to pick up the new code:

```powershell
docker compose restart app
```

Or for a full rebuild if needed:

```powershell
docker compose down
docker compose up -d
```

### Step 3: Generate Migration Automatically

Let Alembic detect the model changes and create the migration file automatically:

```powershell
docker compose exec app alembic revision --autogenerate -m "Add rate_type to ShopProgramRate"
```

This will:

- Compare current database schema with SQLAlchemy models
- Detect differences automatically
- Generate a migration file in `migrations/versions/`
- Include proper upgrade() and downgrade() functions

### Step 4: Review and Fix Migration File

Check the generated migration file in `migrations/versions/` to ensure:

- Column types are correct
- Nullable/default values are appropriate
- Foreign keys are properly defined
- Downgrade function is complete
- **Handle existing data properly** when adding NOT NULL columns

**Important:** When adding a NOT NULL column to a table with existing data:

1. Add the column as nullable first
2. Update existing rows with a default value
3. Then alter the column to be non-nullable

Example:

```python
def upgrade() -> None:
    # Add column as nullable first
    op.add_column('table_name', sa.Column('new_column', sa.String(), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE table_name SET new_column = 'default_value' WHERE new_column IS NULL")
    # Now make it non-nullable
    op.alter_column('table_name', 'new_column', nullable=False)
```

### Step 5: Apply Migration

Apply the migration to update the database schema:

```powershell
docker compose exec app alembic upgrade head
```

### Step 6: Test Application

Restart the container to ensure everything works:

```powershell
docker compose restart app
```

Verify the application is running correctly:

```powershell
docker compose logs app --tail=50
```

### Important Notes

1. **Always review auto-generated migrations** - Alembic might not detect all edge cases
2. **Test migrations in development first** before applying to production
3. **Keep migration messages descriptive** for easier tracking
4. **Don't manually edit model and database** - always use migrations
5. **Commit migration files to git** along with model changes

### Common Alembic Commands

```powershell
# Check current migration status
docker compose exec app alembic current

# View migration history
docker compose exec app alembic history

# Downgrade one revision
docker compose exec app alembic downgrade -1

# Upgrade to specific revision
docker compose exec app alembic upgrade <revision>

# Show SQL without executing
docker compose exec app alembic upgrade head --sql
```

### Recent Changes Log

#### 2026-01-21: Added rate_type to ShopProgramRate

- **Model Changes:** Added `rate_type` column to distinguish between 'shop' and 'contract' rates
- **Scraper Updates:** Modified `base.py` to extract and store rate_type from scraper data
- **Route Updates:** Updated contract evaluation logic in `public.py` to filter by rate_type
- **Template Updates:** Enhanced contract results display in `result.html`
- **Migration:** Auto-generated via `alembic revision --autogenerate -m "Add rate_type to ShopProgramRate"`
- **Fix Applied:** Modified migration to handle existing data by adding column as nullable, updating rows, then making non-nullable

---

## Version Management & Bumping Workflow

**Single Source of Truth Principle:** Version is defined ONLY in pyproject.toml. All other locations (code, Docker, dev env) read from or sync with this single source.

### Version Locations (Read-Only except pyproject.toml)

- **pyproject.toml** \[project] version = "0.3.1"\ **SINGLE SOURCE OF TRUTH**
- **spo/version.py** Reads from pyproject.toml via importlib.metadata.version()
- **.env** Synced from pyproject.toml via scripts/sync_version.py
- **docker-build.sh/ps1** Reads from pyproject.toml for production/CI builds
- **docker-compose.yml** Uses \ fallback

### Version Bump Workflow (3 Simple Steps)

**Step 1: Edit pyproject.toml**

\\\ oml
[project]
version = "0.3.2" # Change ONLY here
\\\

**Step 2: Sync to .env for Local Development**

\\\powershell
python scripts/sync_version.py
\\\

Output:
\\\
 Found version in pyproject.toml: 0.3.2
Updated C:\...\shopping_points_optimiser\.env with version 0.3.2
\\\

**Step 3: Verify in Docker**

\\\powershell
docker compose down
docker compose up -d
docker compose exec app python -c "from spo.version import **version**; print(**version**)"

# Expected output: 0.3.2 (NOT 0.3.2-dev)

\\\

If output shows "-dev", the package wasn't installed in Docker:

- Ensure pip install -e . is in Dockerfile (after dependencies)
- Rebuild: docker compose build app

### Important Notes

1. **Never manually edit .env version** - It's auto-synced, changes will be overwritten
2. **Always run sync script** before testing locally - python scripts/sync_version.py
3. **Commit pyproject.toml + .env together** after sync - They must stay in sync
4. **Production/CI uses pyproject.toml directly** - docker-build.sh reads it automatically
5. **The "-dev" fallback only triggers if package not installed** - This is caught during Docker build

### Commit Message Template for Version Bumps

\\\
chore: bump version to 0.3.2

- Updated pyproject.toml [project] version
- Synced to .env via scripts/sync_version.py
- Verified version in Docker container: 0.3.2
  \\\

### Common Version Bump Issues

**Problem:** Version shows as "0.3.1-dev" in container

- **Cause:** \importlib.metadata.version()\ failed, using fallback
- **Fix:** Ensure Dockerfile has \pip install -e .\ after dependencies
- **Rebuild:** \docker compose build app\

**Problem:** .env not updated after editing pyproject.toml

- **Cause:** Forgot to run sync script
- **Fix:** \python scripts/sync_version.py\

**Problem:** docker-compose.yml shows different version than APP_VERSION

- **Cause:** Fallback \:latest\ tag in use
- **Fix:** Ensure \docker compose build app\ ran after pyproject.toml change
- **Or:** Manually set: \docker build -t shopping-points-optimiser:0.3.2 .\

#### 2026-01-28: Single Source of Truth for Version Management

- **refactored:** Version management to follow best practices (DRY principle)
- **created:** \scripts/sync_version.py\ to auto-sync version from pyproject.toml to .env
- **updated:** Dockerfile to install package with \pip install -e .\ for importlib.metadata support
- **removed:** Hardcoded version from .env (git-tracked)
- **documented:** Version bump workflow in this agent file
