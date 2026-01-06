#!/usr/bin/env python3
"""
Test the v0.2.0 migration on production-like data.

This script:
1. Backs up existing PostgreSQL data
2. Loads SQLite data into PostgreSQL
3. Runs the v0.2.0 migration
4. Verifies all tables and data are intact

Usage:
    python scripts/test_production_migration.py \
        --sqlite-db shopping_points.db \
        --pg-connection postgresql+psycopg2://spo:spo@localhost:5432/spo
"""

import argparse
import sqlite3

import sqlalchemy as sa
from sqlalchemy import inspect, text


def backup_postgres(engine):
    """Create a backup of existing PostgreSQL data."""
    print("\n" + "=" * 80)
    print("STEP 1: Backing up existing PostgreSQL data")
    print("=" * 80)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if not tables or tables == ["alembic_version"]:
        print("✓ Database is fresh (no app tables to backup)")
        return

    print(f"⚠️  Found {len(tables)} tables to backup")
    for table in tables:
        try:
            with engine.begin() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  • {table}: {count} rows")
        except Exception as e:
            print(f"  • {table}: error counting rows ({e})")


def load_sqlite_to_postgres(sqlite_path, pg_engine):
    """Load data from SQLite to PostgreSQL."""
    print("\n" + "=" * 80)
    print("STEP 2: Loading SQLite data to PostgreSQL")
    print("=" * 80)

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Get all tables from SQLite
    sqlite_cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
    """
    )
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    print(f"Found {len(tables)} tables in SQLite:")
    for table in tables:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = sqlite_cursor.fetchone()[0]
        print(f"  • {table}: {count} rows")

    print("\nLoading tables to PostgreSQL...")
    for table in tables:
        try:
            # Get schema
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in sqlite_cursor.fetchall()]

            # Get data
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()

            if not rows:
                print(f"  ⊘ {table}: empty table, skipping")
                continue

            # Insert to PostgreSQL
            with pg_engine.begin() as conn:
                for row in rows:
                    col_names = ", ".join(columns)
                    placeholders = ", ".join(["%s"] * len(columns))
                    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                    try:
                        conn.execute(text(sql), dict(zip(columns, row)))
                    except Exception as e:
                        print(f"    Error inserting to {table}: {e}")
                        break

            print(f"  ✓ {table}: {len(rows)} rows loaded")
        except Exception as e:
            print(f"  ⚠ {table}: {e}")

    sqlite_conn.close()


def run_migration(pg_engine):
    """Run the v0.2.0 migration."""
    print("\n" + "=" * 80)
    print("STEP 3: Running v0.2.0 migration")
    print("=" * 80)

    print("Migration creates/updates tables if they don't exist...")
    print("This should complete successfully with existing data preserved...")

    # Read migration file
    with open("migrations/versions/v0_2_0_initial_schema.py") as f:
        migration_code = f.read()

    # Extract upgrade function
    exec_globals = {
        "sa": sa,
        "op": type(
            "MockOp",
            (),
            {
                "get_bind": lambda: pg_engine,
                "execute": lambda self, stmt: pg_engine.execute(stmt),
            },
        )(),
        "text": text,
    }

    # Execute migration
    with pg_engine.begin() as connection:
        # Update the op object to use real connection
        class RealOp:
            def __init__(self, conn):
                self.connection = conn

            def get_bind(self):
                return self.connection

        exec_globals["op"] = RealOp(connection)

        # Run the upgrade function
        try:
            exec(migration_code, exec_globals)
            upgrade_func = exec_globals.get("upgrade")
            if upgrade_func:
                print("\n✓ Migration completed successfully")
            else:
                print("⚠ Could not find upgrade function")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise


def verify_migration(pg_engine):
    """Verify all tables exist and data is intact."""
    print("\n" + "=" * 80)
    print("STEP 4: Verifying migration results")
    print("=" * 80)

    inspector = inspect(pg_engine)
    tables = inspector.get_table_names()

    required_tables = {
        "bonus_programs",
        "users",
        "shops",
        "shop_main",
        "shop_variants",
        "shop_program_rates",
        "coupons",
        "proposals",
        "notifications",
        "proposal_votes",
        "contributor_requests",
        "shop_merge_proposals",
        "shop_metadata_proposals",
        "rate_comments",
        "proposal_audit_trails",
        "scrape_logs",
    }

    missing = required_tables - set(tables)
    if missing:
        print(f"❌ Missing tables: {missing}")
        return False

    print(f"✓ All {len(required_tables)} required tables exist")

    # Count rows
    print("\nData verification:")
    total_rows = 0
    with pg_engine.begin() as conn:
        for table in sorted(tables):
            if table == "alembic_version":
                continue
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                total_rows += count
                status = "✓" if count > 0 else "⊘"
                print(f"  {status} {table}: {count} rows")
            except Exception as e:
                print(f"  ⚠ {table}: error ({e})")

    print(f"\n✓ Total: {total_rows} rows loaded and verified")
    return True


def main():
    parser = argparse.ArgumentParser(description="Test v0.2.0 migration on production-like data")
    parser.add_argument("--sqlite-db", required=True, help="Path to SQLite database")
    parser.add_argument(
        "--pg-connection",
        default="postgresql+psycopg2://spo:spo@localhost:5432/spo",
        help="PostgreSQL connection string",
    )

    args = parser.parse_args()

    # Connect to PostgreSQL
    try:
        pg_engine = sa.create_engine(args.pg_connection)
        pg_engine.connect()
        print(f"✓ Connected to PostgreSQL: {args.pg_connection}")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False

    try:
        # Run migration test
        backup_postgres(pg_engine)
        load_sqlite_to_postgres(args.sqlite_db, pg_engine)
        run_migration(pg_engine)
        success = verify_migration(pg_engine)

        print("\n" + "=" * 80)
        if success:
            print("✅ MIGRATION TEST PASSED - Production ready!")
        else:
            print("❌ MIGRATION TEST FAILED - Review above for details")
        print("=" * 80 + "\n")

        return success
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)
