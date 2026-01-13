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

if config.config_file_name:
    fileConfig(config.config_file_name)


# --- Robust Alembic DB URL selection for test and dev ---
import os  # noqa: E402

test_db_url = os.environ.get("TEST_DATABASE_URL")
if test_db_url:
    # Always prefer TEST_DATABASE_URL for test runs
    os.environ["DATABASE_URL"] = test_db_url
    os.environ["SQLALCHEMY_DATABASE_URI"] = test_db_url
    config.set_main_option("sqlalchemy.url", test_db_url)
else:
    # Fallback to DATABASE_URL or app config
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        os.environ["SQLALCHEMY_DATABASE_URI"] = db_url
        config.set_main_option("sqlalchemy.url", db_url)

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
