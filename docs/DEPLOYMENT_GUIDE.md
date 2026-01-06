# Production Deployment Guide for v0.2.0

⚠️ **IMPORTANT: This is a FRESH SCHEMA migration - read carefully before deploying!**

## Migration Overview

The v0.2.0 migration (`migrations/versions/v0_2_0_initial_schema.py`) is the **first and only migration** in the project. It creates all 17 application tables from scratch.

### Key Characteristics

- **Type**: Fresh schema initialization
- **Down Revision**: None (first migration)
- **Contains**: All-or-nothing table creation
- **Idempotent**: NO ❌ (will fail if tables already exist)
- **Reversible**: YES (downgrade() deletes all tables)

## Deployment Scenarios

### Scenario 1: Fresh Database (Recommended) ✅

**Status**: Empty PostgreSQL database, no tables

**Deploy Steps**:
```bash
# Run pre-deployment check
python scripts/pre_deployment_check.py

# Expected output: "✅ Database appears to be fresh"

# Deploy with docker-compose
docker-compose up -d

# Verify
docker-compose exec db psql -U spo -d spo -c "\dt"
# Should show 17 tables
```

**Risk Level**: LOW

---

### Scenario 2: Incomplete Migration (Alembic Only) ⚠️

**Status**: Database exists, only `alembic_version` table present

**Cause**: Previous migration run failed or was incomplete

**Deploy Steps**:
```bash
# Run pre-deployment check
python scripts/pre_deployment_check.py

# Expected output: "⚠️ Database has alembic_version table but no app tables"

# Deploy normally
docker-compose up -d

# Migration will create all missing tables
```

**Risk Level**: MEDIUM - Recommended to verify migration history

---

### Scenario 3: Existing Application Tables ❌ CRITICAL

**Status**: Database has app tables from previous version

**Cause**: This is a v0.1.0 → v0.2.0 upgrade on existing deployment

**Problem**: v0.2.0 migration uses `CREATE TABLE` - it WILL FAIL with:
```
Error: relation "shops" already exists
```

**Solutions**:

#### Option A: Fresh Deployment (Recommended if no data needed)
```bash
# 1. Stop application
docker-compose down

# 2. Delete database volume
docker volume rm shopping_points_optimiser_pgdata

# 3. Deploy fresh
docker-compose up -d

# This creates a clean database with v0.2.0 schema
```

#### Option B: Upgrade with Data Preservation (Future - NOT available yet)
```
Status: NOT YET IMPLEMENTED

This would require:
- An incremental migration (v0.1.0_to_v0.2.0)
- Schema comparison between versions
- Data migration logic
- Extensive testing

Do NOT attempt without proper migration file!
```

**Risk Level**: CRITICAL ❌

---

## Pre-Deployment Checklist

Run this before deploying to production:

```bash
# 1. Check database safety
python scripts/pre_deployment_check.py

# 2. Verify locally with test data
docker-compose down -v
docker-compose up -d
docker-compose exec shopping-points python -m pytest tests/test_smoke.py -v

# 3. Check CI pipeline passes
# View: https://github.com/kduchrow/shopping_points_optimiser/actions
# All jobs must be green: lint, version-check, type-check, test, smoke-test

# 4. Verify git state
git status  # Should be clean
git log --oneline -3  # Show last 3 commits
```

---

## Rollback Plan

If deployment fails:

```bash
# Check logs
docker-compose logs shopping-points --tail=100

# If migration failed during alembic step:
# 1. Check which revision was marked
docker-compose exec db psql -U spo -d spo -c "SELECT version FROM alembic_version;"

# 2. Downgrade (careful - this deletes all tables!)
docker-compose exec shopping-points alembic downgrade -1

# 3. Fix issues and retry
```

**WARNING**: Downgrade will delete ALL application data!

---

## Database State Diagram

```
Fresh DB           Incomplete       Existing App
(OK to deploy)     (OK to deploy)   (FAIL - CRITICAL)
    │                   │                  │
    v                   v                  v
 No tables         Only alembic        App tables
    │                   │                  │
    └───────────────────┴──────────────────┘
                        │
         ┌──────────────┴──────────────┐
         │                             │
      DEPLOY v0.2.0               STOP! Pick
      Creates all                Solution A/B
      tables
         │
         v
    Alembic marks
    v0_2_0 complete
         │
         v
    ✅ Success
```

---

## Verification After Deployment

```bash
# Check migration status
docker-compose exec shopping-points alembic current
# Expected: "v0_2_0 (head)"

# Count tables
docker-compose exec db psql -U spo -d spo -c "
SELECT count(*) as table_count
FROM pg_tables
WHERE schemaname = 'public';"
# Expected: 17 (or 18 with alembic_version)

# Test app endpoint
curl -s http://localhost:5000 -w "\nStatus: %{http_code}\n"
# Expected: Status: 200

# Run smoke tests
docker-compose exec shopping-points python -m pytest tests/test_smoke.py -v
# Expected: 11 passed
```

---

## Troubleshooting

### "relation 'shops' does not exist"

**Cause**: Migration didn't run or only partially ran

**Fix**:
```bash
# Check migration status
docker-compose exec shopping-points alembic current

# If stuck on wrong revision, check history
docker-compose exec shopping-points alembic history

# If stuck on v0_2_0 but tables don't exist:
# 1. Get revision ID
REVISION=$(docker-compose exec -T shopping-points alembic heads | grep v0_2_0 | awk '{print $1}')

# 2. Downgrade and upgrade again
docker-compose exec shopping-points alembic downgrade -1
docker-compose exec shopping-points alembic upgrade head
```

### "duplicate key value violates unique constraint"

**Cause**: Data import conflict (shouldn't happen on fresh DB)

**Fix**: Restore from backup or contact database team

### Migration hangs or times out

**Cause**: Large table creation on slow server

**Fix**: Increase timeout and check server resources
```bash
docker-compose up -d --timeout 300
```

---

## Migration Details

| Component | Value |
|-----------|-------|
| Revision ID | v0_2_0 |
| App Version | 0.2.0 |
| Total Tables | 17 |
| Foreign Keys | 15+ |
| Indexes | 5+ |
| Constraints | Unique + Primary keys |
| Data Seeds | None (Alembic only) |
| Downgrade Support | YES (destructive) |

---

## Contact & Support

For deployment issues:
1. Check logs: `docker-compose logs -f`
2. Run diagnostic: `python scripts/pre_deployment_check.py`
3. Review this guide: Scenarios section
4. Contact: [Your DevOps/DBA team]

---

## Version History

- **v0.2.0** (2026-01-06): Initial schema migration
  - Fresh schema creation
  - SQLAlchemy 2.0 compatible
  - All 17 tables defined

---

**Last Updated**: 2026-01-06
**Author**: Development Team
**Status**: ⚠️ PRODUCTION READY - Fresh deployments only
