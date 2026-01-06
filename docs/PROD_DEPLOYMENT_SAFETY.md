# v0.2.0 Production Safety Analysis

**Status**: ⚠️ **CONDITIONAL SAFE** - Depends on your current prod environment

## Quick Answer

**Can you safely deploy v0.2.0 to your prod server?**

| Scenario | Safe? | Action |
|----------|-------|--------|
| **Fresh DB** (no tables) | ✅ YES | Deploy directly |
| **Only alembic_version** | ✅ YES | Deploy directly |
| **Has existing app tables** | ❌ NO | See below |

---

## The Root Issue

The v0.2.0 migration is a **"fresh schema" migration** - it creates all 17 tables from scratch using `CREATE TABLE` statements.

**Problem**: If your prod database already has these tables, the migration **WILL FAIL** with:
```
Error: relation "shops" already exists
```

This happens because `CREATE TABLE` fails if the table already exists.

---

## How to Check Your Prod Server

1. **Connect to your prod database:**
   ```bash
   psql -U [user] -h [prod-host] -d [database] -c "\dt"
   ```

2. **Count the tables:**
   - If 0 tables → ✅ Safe to deploy
   - If only `alembic_version` → ✅ Safe to deploy
   - If 8+ app tables → ❌ **STOP** - Don't deploy!

3. **Run the safety check (if you have database access):**
   ```bash
   DATABASE_URL="postgresql+psycopg2://user:pass@host:5432/db" \
   python scripts/pre_deployment_check.py
   ```

---

## Deployment Scenarios

### ✅ Scenario 1: Fresh Production Database

**Your situation**: New prod server or migrated to fresh database

**What happens**: Migration creates all 17 tables ✅

**Deploy steps**:
```bash
git pull origin main
docker-compose up -d
# App is ready
```

### ✅ Scenario 2: Only Alembic Version Exists

**Your situation**: Previous migration attempt left alembic_version but no tables

**What happens**: Migration creates all 17 tables ✅

**Deploy steps**:
```bash
git pull origin main
docker-compose up -d
# App is ready
```

### ❌ Scenario 3: Existing Application Data (Most Likely!)

**Your situation**: Running v0.1.0 or similar with live data in prod

**What happens**: Migration FAILS with "relation already exists" ❌

**Why it's a problem**:
- v0.2.0 migration is `CREATE TABLE` based
- It's designed for fresh schema initialization
- We didn't write an incremental migration (v0.1.0 → v0.2.0)

**What you need to do**:

#### Option A: Fresh Deployment (Fastest, loses data)
```bash
# This drops everything and starts fresh
docker-compose down -v
git pull origin main
docker-compose up -d
# All data is lost! ⚠️
```

#### Option B: Preserve Data (Requires incremental migration)
```
Status: NOT READY YET

To support existing deployments, we need:
1. An incremental migration script
2. Schema diff analysis
3. Data migration strategy
4. Extensive testing

This is a future enhancement.
```

---

## What Actually Happens on Deploy?

### Fresh DB Flow ✅
```
docker-compose up -d
  ↓
Container starts
  ↓
docker-entrypoint.sh runs alembic upgrade head
  ↓
v0_2_0 migration executes
  ↓
All CREATE TABLE statements succeed
  ↓
Alembic marks v0_2_0 as current
  ↓
App starts
  ↓
✅ Success - App is running with fresh schema
```

### Existing Tables Flow ❌
```
docker-compose up -d
  ↓
Container starts
  ↓
docker-entrypoint.sh runs alembic upgrade head
  ↓
v0_2_0 migration executes
  ↓
CREATE TABLE "shops" fails (already exists)
  ↓
Migration rolls back
  ↓
App fails to start
  ↓
❌ Internal Server Error 500
```

---

## The Safety Check Results

I ran the pre-deployment check on local environment with fresh migration:

```
⚠️ WARNING: Application tables already exist!
   - Found 8 app tables

⚠️ IMPORTANT: v0.2.0 migration uses CREATE TABLE (not ALTER)
- It WILL FAIL if tables already exist

Risk level: CRITICAL - DO NOT DEPLOY WITHOUT ACTION
```

This confirms: **If you have existing tables, deployment will fail.**

---

## Recommended Actions

### Immediate (Before PR Merge)

- [ ] Document which scenario applies to YOUR prod server
- [ ] Determine if you can afford fresh deployment (data loss)
- [ ] If not, discuss timeline for incremental migration

### Short Term (Next Sprint)

- [ ] If fresh deployments OK: proceed with merge
- [ ] If need data preservation: request incremental migration
- [ ] Add to runbook: "v0.2.0 is fresh schema only"

### Long Term

- [ ] Implement incremental migration support
- [ ] Add schema versioning to CI/CD
- [ ] Test all deployment scenarios automatically

---

## Files to Review

- **Migration**: [migrations/versions/v0_2_0_initial_schema.py](../migrations/versions/v0_2_0_initial_schema.py)
  - Uses `CREATE TABLE` (not idempotent)
  - Has `downgrade()` (destructive)

- **Safety Check**: [scripts/pre_deployment_check.py](../scripts/pre_deployment_check.py)
  - Detects scenario automatically
  - Safe to run on any environment

- **Deployment Guide**: [docs/DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
  - Detailed steps for each scenario
  - Troubleshooting guide

---

## Bottom Line

**❓ Can you deploy to prod?**

✅ **YES** - IF your prod database is fresh/empty

❌ **NO** - IF your prod database has existing tables/data

**Check your prod database first!** Use:
```bash
psql -h [prod-host] -U [user] -d [db] -c "\dt"
```

If it shows app tables → you need a different solution first.

---

**Last Updated**: 2026-01-06
**Created By**: Development Team
**Status**: Ready for review before merge
