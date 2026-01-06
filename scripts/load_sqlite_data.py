#!/usr/bin/env python3
"""
Load SQLite production data into PostgreSQL.

Usage:
    python scripts/load_sqlite_data.py instance/shopping_points.db postgresql+psycopg2://spo:spo@localhost:5432/spo
"""

import sqlite3
import sys

import sqlalchemy as sa
from sqlalchemy import text


def load_sqlite_to_postgres(sqlite_path, pg_connection_string):
    """Load data from SQLite to PostgreSQL."""
    print("\n" + "=" * 80)
    print("Loading SQLite data to PostgreSQL")
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
        AND name NOT LIKE 'alembic_version'
    """
    )
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    print(f"\nFound {len(tables)} tables in SQLite:")
    for table in tables:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = sqlite_cursor.fetchone()[0]
        print(f"  • {table}: {count} rows")

    # Connect to PostgreSQL
    pg_engine = sa.create_engine(pg_connection_string)

    print("\nCreating tables in PostgreSQL...")
    for table in tables:
        try:
            # Get schema from SQLite
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = sqlite_cursor.fetchall()

            # Build CREATE TABLE statement
            col_defs = []
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                col_notnull = col[3]
                col_pk = col[5]

                # Map SQLite types to PostgreSQL
                pg_type = col_type.upper()
                if "INT" in pg_type:
                    pg_type = "INTEGER"
                elif "CHAR" in pg_type or "TEXT" in pg_type:
                    pg_type = "VARCHAR"
                elif "REAL" in pg_type or "FLOAT" in pg_type or "DOUBLE" in pg_type:
                    pg_type = "FLOAT"
                elif "BLOB" in pg_type:
                    pg_type = "BYTEA"

                col_def = f"{col_name} {pg_type}"
                if col_pk:
                    if "INTEGER" in pg_type:
                        col_def = f"{col_name} SERIAL PRIMARY KEY"
                    else:
                        col_def += " PRIMARY KEY"
                elif col_notnull:
                    col_def += " NOT NULL"

                col_defs.append(col_def)

            create_sql = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(col_defs)})"

            with pg_engine.begin() as conn:
                conn.execute(text(create_sql))

            print(f"  ✓ {table}: table created")
        except Exception as e:
            print(f"  ⚠ {table}: error creating table ({e})")
            continue

    print("\nLoading data to PostgreSQL...")
    for table in tables:
        try:
            # Get column names
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
                    placeholders = ", ".join([f":{col}" for col in columns])
                    sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"
                    try:
                        conn.execute(text(sql), dict(zip(columns, row)))
                    except Exception as e:
                        print(f"    Error inserting to {table}: {e}")
                        # Continue with next row
                        continue

            print(f"  ✓ {table}: {len(rows)} rows loaded")
        except Exception as e:
            print(f"  ⚠ {table}: {e}")

    sqlite_conn.close()

    # Verify
    print("\n" + "=" * 80)
    print("Verification:")
    print("=" * 80)

    total_rows = 0
    with pg_engine.begin() as conn:
        for table in sorted(tables):
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                total_rows += count
                status = "✓" if count > 0 else "⊘"
                print(f"  {status} {table}: {count} rows")
            except Exception as e:
                print(f"  ⚠ {table}: error ({e})")

    print(f"\n✓ Total: {total_rows} rows loaded")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/load_sqlite_data.py <sqlite-path> <pg-connection>")
        sys.exit(1)

    load_sqlite_to_postgres(sys.argv[1], sys.argv[2])
