import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add parent directory to path so we can import spo module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spo import create_app  # noqa: E402
from spo.extensions import db  # noqa: E402

config = context.config


import os  # noqa: E402

# --- Robust Alembic DB URL selection for test and dev ---
if config.config_file_name:
    fileConfig(config.config_file_name)

# Read raw value from alembic.ini without interpolation
raw_ini_url = None
if config.file_config.has_option("alembic", "sqlalchemy.url"):
    raw_ini_url = config.file_config.get("alembic", "sqlalchemy.url", raw=True)

# Get DB URL from environment
db_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")

# Substitute %(DATABASE_URL)s manually if present
if raw_ini_url and "%(DATABASE_URL)s" in raw_ini_url:
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)
    else:
        raise RuntimeError("DATABASE_URL must be set in environment for Alembic migrations.")
elif db_url:
    config.set_main_option("sqlalchemy.url", db_url)
elif raw_ini_url:
    config.set_main_option("sqlalchemy.url", raw_ini_url)

app = create_app(start_jobs=False, run_seed=False)
with app.app_context():
    from spo import models  # noqa: F401

    # If not already set, set Alembic DB URL from app config
    if not config.get_main_option("sqlalchemy.url"):
        config.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])
    target_metadata = db.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
