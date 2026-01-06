# SQLite to PostgreSQL Migration Guide

This document outlines how to migrate your Shopping Points Optimiser deployment from SQLite to PostgreSQL.

## Prerequisites

- Docker and Docker Compose installed and running
- Existing SQLite database at `instance/shopping_points.db`
- PostgreSQL image (postgres:16-alpine) available
- **IMPORTANT:** Ensure `psycopg2-binary` is in `requirements.txt` (already included in the project)

## Migration Steps

### 0. Rebuild Docker Image (REQUIRED)

**⚠️ CRITICAL:** You must rebuild the Docker image to install the PostgreSQL driver (`psycopg2-binary`):

```bash
docker-compose build shopping-points
```

This ensures `psycopg2-binary` from `requirements.txt` is installed in the container. **Skipping this step will cause a `ModuleNotFoundError: No module named 'psycopg2'` error.**

### 1. Update Environment Configuration

Edit your `.env` file and set the database URL to PostgreSQL:

```bash
DATABASE_URL=postgresql+psycopg2://spo:spo@db:5432/spo
```

**Note:** Replace `spo:spo` with your desired username and password if different, and ensure it matches the `docker-compose.yml` environment variables.

### 2. Start the Database Service

If not already running, start the PostgreSQL container:

```bash
docker-compose up -d db
```

Verify the database is healthy:

```bash
docker-compose ps
```

The `shopping-points-db` container should show status `healthy`.

### 3. Initialize Database Schema

Run Alembic migrations to create all tables in the new PostgreSQL database:

```bash
docker-compose exec shopping-points python -m alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 20240106_0001, Initial schema
```

### 4. Migrate Data from SQLite to PostgreSQL

**⚠️ IMPORTANT:** This step will fail if you already have data in PostgreSQL. If re-running, see [Troubleshooting: duplicate key error](#duplicate-key-value-violates-unique-constraint-users_pkey-error) below.

Run the migration script inside the app container:

```bash
docker-compose exec shopping-points python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path /app/instance/shopping_points.db \
  --target-url postgresql+psycopg2://spo:spo@db:5432/spo
```

Expected output shows tables being copied:
```
📁 Source (sqlite): /app/instance/shopping_points.db
🎯 Target (db): postgresql+psycopg2://spo:spo@db:5432/spo
ℹ️  Skipping alembic_version: managed separately
➡️  Copying 1 rows from users...
➡️  Copying 3 rows from bonus_programs...
➡️  Copying 1 rows from shops...
➡️  Copying 3 rows from shop_program_rates...
✅ Migration completed
```

### 5. Restart the Application

**⚠️ If you skipped Step 0, the app will crash with `ModuleNotFoundError: No module named 'psycopg2'`.**

Rebuild (if not done in Step 0) and restart the app container with the updated database URL:

```bash
docker-compose build shopping-points
docker-compose up -d --force-recreate shopping-points
```

Wait for the container to become healthy (typically 40 seconds):

```bash
docker-compose ps
```

The `shopping-points-optimiser` container should show `(healthy)` status.

### 6. Verify the Migration

Check that data was correctly migrated by running a quick query:

```bash
docker-compose exec shopping-points python -c \
  "from spo import create_app; from spo.models import User, BonusProgram, Shop, ShopProgramRate; \
   app=create_app(start_jobs=False, run_seed=False); \
   ctx=app.app_context(); ctx.push(); \
   print('users:', User.query.count()); \
   print('bonus_programs:', BonusProgram.query.count()); \
   print('shops:', Shop.query.count()); \
   print('shop_program_rates:', ShopProgramRate.query.count()); \
   ctx.pop()"
```

Expected output (example):
```
users: 1
bonus_programs: 3
shops: 1
shop_program_rates: 3
```

### 7. Verify Web Application

Open your browser and navigate to `http://localhost:5000` (or your configured URL). Log in and verify that:
- Users and credentials are present
- Shops and bonus programs display correctly
- No data appears corrupted or missing

## Troubleshooting

### "ModuleNotFoundError: No module named 'psycopg2'" Error

**Cause:** The Docker image was not rebuilt after adding `psycopg2-binary` to `requirements.txt`, or the requirements weren't installed.

**Fix:**
```bash
# Rebuild the Docker image to install psycopg2-binary
docker-compose build shopping-points

# Restart the container
docker-compose up -d --force-recreate shopping-points
```

Verify the module is installed:
```bash
docker-compose exec shopping-points python -c "import psycopg2; print(psycopg2.__version__)"
```

### "No tables found on target" Error

**Cause:** Alembic migrations haven't been applied to the PostgreSQL database.

**Fix:**
```bash
docker-compose exec shopping-points python -m alembic upgrade head
```

Then retry the migration script.

### "duplicate key value violates unique constraint" Error

**Cause:** The alembic_version table already has an entry.

**Fix:** This is handled automatically by the migration script (it skips `alembic_version`). If you encounter this error, ensure you're using the latest version of `scripts/migrate_sqlite_to_postgres.py`.

### "duplicate key value violates unique constraint 'users_pkey'" Error

**Cause:** You're trying to migrate data into a PostgreSQL database that already contains data. This happens when re-running the migration script.

**Fix Option 1 - Clear PostgreSQL tables (DESTRUCTIVE):**
```bash
# First, get list of all tables
docker-compose exec db psql -U spo -d spo -c "\dt"

# Truncate only existing tables (adjust list based on your schema)
docker-compose exec db psql -U spo -d spo -c "
TRUNCATE TABLE users, bonus_programs, shops, shop_program_rates CASCADE;
"
```

If you have additional tables (coupons, proposals, etc.), add them to the TRUNCATE command.

Then retry the migration script from Step 4.

**Fix Option 2 - Drop and recreate the database (DESTRUCTIVE, RECOMMENDED):**
```bash
# Stop the app
docker-compose stop shopping-points

# Drop and recreate the database
docker-compose exec db psql -U spo -d postgres -c "DROP DATABASE IF EXISTS spo;"
docker-compose exec db psql -U spo -d postgres -c "CREATE DATABASE spo;"

# Start the app (or just start it to run migrations)
docker-compose start shopping-points

# Re-run migrations
docker-compose exec shopping-points python -m alembic upgrade head

# Retry the migration from Step 4
```

### Connection Refused / Cannot Connect to Database

**Cause:** PostgreSQL container is not running or not healthy.

**Fix:**
```bash
docker-compose logs db
docker-compose up -d db
docker-compose ps db
```

Wait for the db container to show `healthy` status.

### "SQLite file not found" Error

**Cause:** The SQLite database file path is incorrect.

**Fix:** Verify the SQLite file exists and update the `--sqlite-path` argument:
```bash
ls -la instance/shopping_points.db
```

## Optional: Cleanup

Once you've verified the migration is successful and the app runs correctly, you may optionally:

1. **Archive the SQLite file** for backup:
   ```bash
   cp instance/shopping_points.db backups/shopping_points.db.backup
   ```

2. **Remove the SQLite file** (if you're confident in the migration):
   ```bash
   rm instance/shopping_points.db
   ```

3. **Update .dockerignore** (already done) to ensure `instance/` and SQLite files don't get into new images.

## Future Deployments

For new deployments:

1. Set `DATABASE_URL=postgresql+psycopg2://spo:spo@db:5432/spo` in `.env` from the start.
2. The Docker Compose startup flow will automatically:
   - Start the PostgreSQL container
   - Run Alembic migrations (`python -m alembic upgrade head`)
   - Launch the Flask app
3. No SQLite migration step needed if starting fresh.

## Reverting (Fallback)

If you need to revert to SQLite for any reason:

1. Update `.env`:
   ```bash
   DATABASE_URL=sqlite:////app/instance/shopping_points.db
   ```

2. Restore from backup (if available):
   ```bash
   cp backups/shopping_points.db.backup instance/shopping_points.db
   ```

3. Restart:
   ```bash
   docker-compose build --no-cache shopping-points
   docker-compose up -d --force-recreate shopping-points
   ```

## Support

For issues or questions about the migration, check:
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- Project README and contributing guidelines
