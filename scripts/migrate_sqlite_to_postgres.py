import argparse
import os
from collections.abc import Sequence

from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.sql.util import sort_tables


def load_sorted_tables(engine) -> list[Table]:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return list(sort_tables(metadata.tables.values()))


def fetch_rows(conn: Connection, table: Table) -> list[dict]:
    result = conn.execute(table.select())
    return [dict(row._mapping) for row in result]


def copy_table(src_conn: Connection, dst_conn: Connection, table: Table, inspector):
    if not inspector.has_table(table.name):
        print(f"⚠️  Skipping {table.name}: not present in source")
        return

    src_table = Table(table.name, MetaData(), autoload_with=src_conn)
    rows = fetch_rows(src_conn, src_table)
    if not rows:
        print(f"ℹ️  {table.name}: no rows to copy")
        return

    print(f"➡️  Copying {len(rows)} rows from {table.name}...")
    dst_conn.execute(table.insert(), rows)

    # Reset sequence if table has an integer PK named 'id'
    if "id" in table.c and str(table.c.id.type).startswith("INTEGER"):
        seq_sql = (
            "SELECT setval(pg_get_serial_sequence(:tbl, 'id'), "
            "(SELECT COALESCE(MAX(id), 0) FROM " + table.name + "))"
        )
        dst_conn.execute(text(seq_sql), {"tbl": table.name})


def migrate(sqlite_path: str, target_url: str):
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"SQLite file not found: {sqlite_path}")

    print(f"📁 Source (sqlite): {sqlite_path}")
    print(f"🎯 Target (db): {target_url}")

    src_engine = create_engine(f"sqlite:///{sqlite_path}")
    dst_engine = create_engine(target_url)

    # Reflect target tables to preserve FK order
    tables: Sequence[Table] = load_sorted_tables(dst_engine)
    if not tables:
        raise RuntimeError("No tables found on target. Run alembic upgrade head first.")

    with src_engine.connect() as src_conn, dst_engine.connect() as dst_conn:
        src_inspector = inspect(src_conn)
        with dst_conn.begin():
            # Temporarily disable triggers to simplify FK ordering
            dst_conn.execute(text("SET session_replication_role = 'replica'"))

            for table in tables:
                if table.name == "alembic_version":
                    print("ℹ️  Skipping alembic_version: managed separately")
                    continue

                copy_table(src_conn, dst_conn, table, src_inspector)

            dst_conn.execute(text("SET session_replication_role = 'origin'"))

    print("✅ Migration completed")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite to Postgres using SQLAlchemy metadata"
    )
    parser.add_argument(
        "--sqlite-path",
        default=os.environ.get("SQLITE_PATH", "instance/shopping_points.db"),
        help="Path to the existing SQLite database (default: instance/shopping_points.db)",
    )
    parser.add_argument(
        "--target-url",
        default=os.environ.get("DATABASE_URL", "postgresql+psycopg2://spo:spo@localhost:5432/spo"),
        help="SQLAlchemy URL for the Postgres database",
    )
    args = parser.parse_args()

    migrate(args.sqlite_path, args.target_url)


if __name__ == "__main__":
    main()
