# Feature Development Workflow

This document outlines the **mandatory** workflow for implementing new features in Shopping Points Optimiser. Following this process ensures code quality, test coverage, and maintainability.

## 📋 Development Process

### 1. 🤔 Understand & Clarify Requirements

**Before writing any code:**

- Read and understand the feature request completely
- Ask clarifying questions about:
  - Expected behavior and edge cases
  - User interface/API requirements
  - Performance considerations
  - Database schema changes needed
  - Integration with existing features
  - Acceptance criteria
- Document the feature requirements clearly
- Get confirmation that requirements are understood correctly

**Questions to Ask:**

- What problem does this feature solve?
- Who are the users of this feature?
- What are the inputs and expected outputs?
- Are there any dependencies on other features?
- What should happen in error cases?
- Are there any security concerns?
- What are the performance requirements?

---

### 2. 🌿 Create Feature Branch

**Branch Naming Convention:**

```bash
git checkout -b feature/<short-descriptive-name>
```

**Examples:**

- `feature/email-notifications`
- `feature/export-results-csv`
- `feature/advanced-search`
- `feature/rate-history-chart`

**Best Practices:**

- Branch from `main` or `develop`
- Keep branch name short but descriptive
- Use lowercase with hyphens
- Prefix with `feature/` for new features
- Use `bugfix/` for bug fixes
- Use `hotfix/` for urgent production fixes

---

### 3. ✅ Write Tests First (TDD Approach)

**Before implementing the feature, write tests:**

#### Test Structure

```python
# tests/test_<feature_name>.py

import pytest
from spo import create_app
from spo.extensions import db

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(start_jobs=False, run_seed=False)
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

def test_feature_happy_path(client):
    """Test the main success scenario."""
    # Arrange: Set up test data

    # Act: Execute the feature

    # Assert: Verify expected behavior
    pass

def test_feature_edge_case_1(client):
    """Test edge case or error condition."""
    pass

def test_feature_validation_error(client):
    """Test validation and error handling."""
    pass
```

#### Test Coverage Requirements

- **Happy path**: Main success scenario
- **Edge cases**: Boundary conditions, empty inputs, null values
- **Error cases**: Invalid inputs, validation failures
- **Integration**: How feature interacts with existing code
- **Security**: Authorization, input sanitization
- **Performance**: If applicable

#### Test Types

1. **Unit Tests**: Test individual functions/methods
2. **Integration Tests**: Test feature with database/external services
3. **API Tests**: Test REST endpoints
4. **UI Tests**: Test user interface behavior (if applicable)

---

### 4. 💻 Implement the Feature

**Implementation Guidelines:**

#### Code Style

- Follow PEP 8 (enforced by ruff/black)
- Use Python 3.11+ type hints: `X | None` instead of `Optional[X]`
- 100 character line length
- Document public APIs with docstrings
- Write clear, self-documenting code

#### Code Organization

```python
# Example structure for a new feature

# spo/routes/feature_name.py
from flask import Blueprint, jsonify, request
from spo.extensions import db
from spo.models import YourModel

feature_bp = Blueprint('feature', __name__)

@feature_bp.route('/api/feature', methods=['GET'])
def get_feature():
    """
    Get feature data.

    Returns:
        JSON response with feature data
    """
    # Implementation
    pass
```

#### Database Changes

If feature requires database changes:

```bash
# Create Alembic migration
python -m alembic revision --autogenerate -m "Add feature_name table"

# Review the generated migration file
# Edit if needed to ensure correctness

# Apply migration in development
python -m alembic upgrade head
```

#### Documentation

- Add inline comments for complex logic
- Document public functions with docstrings
- Update relevant documentation files
- Add usage examples if applicable

---

### 5. 🧪 Run Tests

**Execute tests to verify implementation:**

**Important: For local development, ensure `.env` has `FLASK_ENV=development`**
This automatically installs dev dependencies (pytest, coverage, etc.) in the Docker container.

#### Quick Test & Rebuild (Recommended)

Use the provided scripts to rebuild, restart, and test:

**PowerShell (Windows):**

```powershell
# Full rebuild and restart
.\scripts\test-rebuild.ps1

# Skip build if no dependencies changed
.\scripts\test-rebuild.ps1 -SkipBuild

# Clean start (removes volumes, fresh database)
.\scripts\test-rebuild.ps1 -CleanStart

# Show more log lines
.\scripts\test-rebuild.ps1 -LogLines 100
```

**Bash (Linux/Mac):**

```bash
# Full rebuild and restart
./scripts/test-rebuild.sh

# Skip build if no dependencies changed
./scripts/test-rebuild.sh --skip-build

# Clean start (removes volumes, fresh database)
./scripts/test-rebuild.sh --clean

# Show more log lines
./scripts/test-rebuild.sh --log-lines 100
```

#### Manual Test Steps

If you need more control:

```bash
# Set development mode in .env
FLASK_ENV=development

# Rebuild container to install dev dependencies
docker-compose build shopping-points

# Restart container
docker-compose restart shopping-points

# Wait for initialization
Start-Sleep -Seconds 15  # PowerShell
# or
sleep 15  # Bash

# Check logs for errors
docker-compose logs shopping-points --tail=40
```

#### Running Tests
#### Running Tests

```bash
# Run all tests
pytest

# In Docker container
docker-compose exec -T shopping-points python -m pytest -q

# Run with coverage
pytest --cov=spo --cov-report=html

# Run specific test file
pytest tests/test_<feature_name>.py

# Run with verbose output
pytest -v

# Run specific test function
pytest tests/test_<feature_name>.py::test_function_name
```

#### If Tests Fail:

**Analyze failure:**

- Read the error message carefully
- Check which assertion failed
- Review the test expectations
- Debug the implementation

**Decision Point:**

- **Test is correct, implementation is wrong** → Go to **Step 4** (fix implementation)
- **Implementation is correct, test is wrong** → Go to **Step 3** (fix test)
- **Both need adjustment** → Iterate between Steps 3 and 4

**Keep iterating until all tests pass ✅**

---

### 6. 🪝 Run Pre-commit Hooks

**Once all tests pass, check code quality:**

```bash
# Run pre-commit on all changed files
pre-commit run

# Run pre-commit on all files (recommended)
pre-commit run --all-files
```

#### Pre-commit Checks

Pre-commit will automatically run:

1. **Trailing whitespace** - Remove trailing spaces
2. **End of files** - Ensure files end with newline
3. **YAML validation** - Check YAML syntax
4. **Large files check** - Prevent committing large files
5. **Merge conflicts** - Detect conflict markers
6. **Debug statements** - Find leftover debug code
7. **Ruff** - Python linting with auto-fix
8. **Ruff format** - Python code formatting
9. **Black** - Code formatter
10. **isort** - Import sorting
11. **Prettier** - Format YAML, JSON, HTML, Markdown
12. **yamllint** - YAML linting
13. **Detect secrets** - Find exposed secrets

#### If Pre-commit Fails:

**Common Failures:**

- **Formatting issues**: Often auto-fixed by pre-commit, run again
- **Linting errors**: Fix code issues (go to Step 4)
- **Type errors**: Add/fix type hints (go to Step 4)
- **Security issues**: Fix secrets or security concerns (go to Step 4)

**Keep running pre-commit until all checks pass ✅**

---

### 7. 🔄 Fix Pre-commit Issues

**If pre-commit fails, go back to Step 4:**

1. Review pre-commit output
2. Fix the reported issues
3. Run tests again (Step 5)
4. Run pre-commit again (Step 6)
5. Repeat until both tests and pre-commit pass

**Common Fixes:**

```bash
# Auto-fix many issues
pre-commit run --all-files

# Manual fixes
# - Type hints: Add proper type annotations
# - Imports: Organize imports properly
# - Line length: Break long lines
# - Docstrings: Add missing documentation
```

---

### 8. 👤 Request User Testing

**Once all automated checks pass:**

1. **Provide testing instructions** to the user:

```markdown
## Feature Ready for Testing

### What's New
[Brief description of the feature]

### How to Test
1. **IMPORTANT**: If static files (CSS, JS) were changed, rebuild the Docker container:
   ```bash
   docker-compose build shopping-points
   docker-compose up -d
   ```
   Note: Simple `docker-compose restart` does NOT update static files!

2. Start the application: `docker-compose up` or `python app.py`
3. Navigate to [URL/Page]
4. [Step-by-step testing instructions]
5. Expected behavior: [What should happen]

### Test Cases to Verify
- [ ] Happy path: [Main scenario]
- [ ] Edge case 1: [Description]
- [ ] Edge case 2: [Description]
- [ ] Error handling: [What to test]

### Database Changes (if any)
- Run migration: `python -m alembic upgrade head`

### Configuration Changes (if any)
- Update .env with: [New variables]
```

2. **Wait for user feedback**
3. **Address any issues** found during testing (return to Step 4)

---

### 9. 📝 Commit & Pull Request

**After successful user testing:**

#### Commit Message Format

```bash
git add .
git commit -m "feat: <short description>

<detailed description of changes>

- Added: [list of additions]
- Changed: [list of changes]
- Fixed: [list of fixes]

Closes #<issue-number>"
```

#### Commit Message Examples

```bash
# Feature addition
git commit -m "feat: add email notification system

Implement email notifications for proposal updates

- Added: EmailService class for sending notifications
- Added: Email templates for proposal events
- Added: SMTP configuration in environment variables
- Changed: Notification model to include email_sent flag
- Fixed: Race condition in notification creation

Tests included for all email scenarios.

Closes #42"

# Bug fix
git commit -m "fix: correct rate calculation with multiple coupons

Fixed incorrect calculation when multiple coupons are active

- Fixed: Coupon stacking logic in rate calculator
- Added: Test cases for coupon combinations
- Changed: Validation to prevent invalid coupon combinations

Closes #87"
```

#### Pull Request Template

**Propose this content for the PR:**

```markdown
## 🎯 Description

[Brief description of what this PR accomplishes]

## 🔗 Related Issue

Closes #[issue number]

## 📋 Changes

### Added
- [List new features/files added]

### Changed
- [List modifications to existing features]

### Fixed
- [List bug fixes]

### Database Changes
- [ ] Requires migration: `python -m alembic upgrade head`
- [ ] No database changes

## ✅ Testing

### Automated Tests
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Coverage: [X]%

### Manual Testing
- [ ] Tested happy path
- [ ] Tested edge cases
- [ ] Tested error handling
- [ ] Cross-browser testing (if UI changes)

### User Acceptance Testing
- [ ] Feature tested by [user name]
- [ ] Feedback addressed

## 🔍 Code Quality

- [ ] All pre-commit hooks passing
- [ ] No linting errors
- [ ] Type hints added
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

## 📸 Screenshots (if applicable)

[Add screenshots of UI changes]

## 🚀 Deployment Notes

### Configuration
- [ ] No configuration changes required
- [ ] Requires .env updates: [list variables]

### Dependencies
- [ ] No new dependencies
- [ ] New dependencies added to requirements.txt

### Breaking Changes
- [ ] No breaking changes
- [ ] Breaking changes: [describe]

## 📝 Checklist

- [ ] Code follows project style guide
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Pre-commit hooks passing
- [ ] User tested and approved

## 👥 Reviewers

@[reviewer-username]

---

**Ready for review and merge into `main`**
```

---

## 📊 Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│  1. Understand & Ask Questions                              │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Create Feature Branch                                   │
│     git checkout -b feature/<name>                          │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Write Tests (TDD)                                       │
│     - Happy path                                            │
│     - Edge cases                                            │
│     - Error handling                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Implement Feature                                       │
│     - Follow code style                                     │
│     - Add type hints                                        │
│     - Document code                                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Run Tests                                               │
│     pytest --cov=spo                                        │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    Tests Pass?      Tests Fail
         │                │
         │                ├──► Fix Test (→ Step 3)
         │                │
         │                └──► Fix Code (→ Step 4)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Run Pre-commit                                          │
│     pre-commit run --all-files                              │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    Pre-commit       Pre-commit
       Pass?           Fails
         │                │
         │                └──► Step 7: Fix Issues (→ Step 4)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  8. Request User Testing                                    │
│     - Provide testing instructions                          │
│     - Wait for feedback                                     │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    User Approves   Issues Found
         │                │
         │                └──► Back to Step 4
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  9. Commit & Create Pull Request                            │
│     - Write clear commit message                            │
│     - Propose PR content                                    │
│     - User creates commit                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Principles

1. **Test-Driven Development (TDD)**: Write tests before implementation
2. **Iterative Process**: Go back and fix issues until everything passes
3. **Code Quality**: Never compromise on pre-commit checks
4. **User Validation**: Always get user approval before committing
5. **Clear Communication**: Document everything clearly
6. **No Shortcuts**: Follow all steps, every time

---

## � Version Bump Checklist

When releasing a new version, update these files **in this order**:

### 1. Update Version Number

**Single Source of Truth:**
- `spo/version.py` - Update `__version__` variable

**Automatically Synced (read from version.py):**
- `setup.py` - Reads from version.py
- `spo/__init__.py` - Imports from version.py
- Web UI footer - Uses Flask config `APP_VERSION`

**Manually Update:**
- `package.json` - Update `"version"` field
- `migrations/versions/vX_Y_Z_*.py` - Migration filename and revision ID
  - Filename: `vX_Y_Z_description.py`
  - Revision ID: `vX_Y_Z`
  - Add `App Version: X.Y.Z` in docstring
- `.env` / `docker-compose.yml` - Set `APP_VERSION=X.Y.Z` for Docker builds

### 2. Update Documentation

- `docs/CHANGELOG.md` - Add new version entry with changes
- `README.md` - Update version badges if present
- `docs/GITHUB_SETUP.md` - Update release examples if needed

### 3. Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR (X.0.0)**: Breaking changes, incompatible API changes
- **MINOR (0.X.0)**: New features, backward-compatible
- **PATCH (0.0.X)**: Bug fixes, backward-compatible

**Examples:**
- SQLAlchemy 1.x → 2.0 migration: `0.1.0` → `0.2.0` (MINOR)
- Bug fix in scraper: `0.2.0` → `0.2.1` (PATCH)
- Complete API rewrite: `0.9.0` → `1.0.0` (MAJOR)

**Docker Image Tagging:**
Images are automatically tagged with:
- `shopping-points-optimiser:X.Y.Z` (specific version)
- `shopping-points-optimiser:latest` (latest build)

Labels include version, build date, and git commit SHA.

### 4. Build Docker Image (Optional)

Use the build scripts for version-tagged images:

**PowerShell (Windows):**
```powershell
.\scripts\docker-build.ps1
```

**Bash (Linux/Mac):**
```bash
./scripts/docker-build.sh
```

These scripts automatically:
- Extract version from `spo/version.py`
- Tag image with version number
- Add OCI-compliant metadata labels
- Show image metadata

Or use docker-compose with version:
```bash
# Set version in .env
echo "APP_VERSION=0.2.0" >> .env

# Build with version
docker-compose build
```

Inspect image metadata:
```bash
docker inspect shopping-points-optimiser:0.2.0 --format='{{json .Config.Labels}}'
```

### 5. Verification

Run the version consistency check:

```bash
# Check version consistency across all files
python scripts/check_version.py
```

Expected output:
```
✅ App Version (spo/version.py): 0.2.0
✅ package.json version: 0.2.0 (matches)
✅ Latest migration revision: v0_2_0 (matches)

🎉 All version checks passed! App is at version 0.2.0
```

Manual checks:
```bash
# Check version in Python
python -c "from spo.version import __version__; print(__version__)"

# Check version in container
docker-compose exec shopping-points python -c "from spo.version import __version__; print(__version__)"

# Verify Web UI displays correct version in footer
```

---

## �🚫 What NOT to Do

- ❌ Skip writing tests
- ❌ Commit without running pre-commit
- ❌ Push code with failing tests
- ❌ Ignore linting errors
- ❌ Skip user testing
- ❌ Write vague commit messages
- ❌ Create oversized PRs (keep features focused)
- ❌ Mix multiple features in one branch

---

## 📚 Additional Resources

- [Testing Documentation](../tests/README.md)
- [Pre-commit Setup](PRE_COMMIT_SETUP.md)
- [Contributing Guide](../README.md#contributing)
- [Code Style Guide](../README.md#code-style)
- [Database Migrations](MIGRATION_SQLITE_TO_POSTGRES.md)

---

## 💡 Tips for Success

- **Small, focused features**: Easier to test and review
- **Regular commits**: Commit after each logical step
- **Clear communication**: Ask questions early and often
- **Read error messages**: They usually tell you exactly what's wrong
- **Use git branches**: Keep main/develop clean
- **Review your own code**: Self-review before requesting user testing
- **Update documentation**: Keep docs in sync with code

---

**Remember: Quality over speed. Following this workflow ensures maintainable, reliable code.**
