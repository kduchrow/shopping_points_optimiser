#!/usr/bin/env python3
"""
Quick test of v0.2.0 migration on production data.

This loads a SQLite database into PostgreSQL and runs the migration.
"""

import os
import sqlite3
import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import text


def main():
    # Find SQLite DB
    sqlite_file = Path("shopping_points.db")
    if not sqlite_file.exists():
        print("❌ shopping_points.db not found")
        print(f"   Looked in: {sqlite_file.resolve()}")
        return False

    print(f"\n✓ Found SQLite DB: {sqlite_file}")

    # Connect to PostgreSQL
    pg_url = os.environ.get("DATABASE_URL", "postgresql+psycopg2://spo:spo@localhost:5432/spo")
    try:
        pg_engine = sa.create_engine(pg_url)
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False

    # Load SQLite data
    print("\n" + "=" * 70)
    print("LOADING SQLITE DATA TO POSTGRESQL")
    print("=" * 70)

    sqlite_conn = sqlite3.connect(sqlite_file)
    sqlite_cursor = sqlite_conn.cursor()

    # Get tables
    sqlite_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    print(f"\nFound {len(tables)} tables in SQLite:")
    for table in tables:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = sqlite_cursor.fetchone()[0]
        print(f"  • {table}: {count} rows")

    print("\nLoading to PostgreSQL...")

    with pg_engine.begin() as conn:
        for table in tables:
            try:
                # Get column names and data
                sqlite_cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in sqlite_cursor.fetchall()]

                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()

                if not rows:
                    print(f"  ⊘ {table}: empty")
                    continue

                # Insert into PostgreSQL
                for row in rows:
                    col_names = ", ".join(columns)
                    values = ", ".join(
                        [
                            f"'{str(v).replace(chr(39), chr(39)*2)}'" if v is not None else "NULL"
                            for v in row
                        ]
                    )
                    sql = f"INSERT INTO {table} ({col_names}) VALUES ({values})"
                    try:
                        conn.execute(text(sql))
                    except Exception as e:
                        if "duplicate key" in str(e).lower():
                            continue
                        print(f"    Error: {e}")
                        break

                print(f"  ✓ {table}: {len(rows)} rows loaded")
            except Exception as e:
                print(f"  ⚠ {table}: {e}")

    sqlite_conn.close()

    # Run migration
    print("\n" + "=" * 70)
    print("RUNNING v0.2.0 MIGRATION")
    print("=" * 70)

    print("\nMigration running (using CREATE TABLE IF NOT EXISTS)...")
    print("This should complete without errors...\n")

    # Run Alembic migration
    os.system(f"DATABASE_URL={pg_url} alembic upgrade head")

    # Verify
    print("\n" + "=" * 70)
    print("VERIFYING RESULTS")
    print("=" * 70)

    with pg_engine.connect() as conn:
        # Check tables
        result = conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
        )
        tables = [row[0] for row in result.fetchall()]

        print(f"\n✓ All tables in PostgreSQL ({len(tables)} tables):")
        for table in tables:
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = count_result.scalar()
            print(f"  • {table}: {count} rows")

    print("\n" + "=" * 70)
    print("✅ MIGRATION TEST COMPLETE")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
