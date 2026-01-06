"""Upgrade database to latest migration revision.
Usage: python scripts/db_upgrade.py
Respects DATABASE_URL env var.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent
ALEMBIC_CFG = BASE_DIR / "alembic.ini"


def upgrade_to_head() -> None:
    cfg = Config(str(ALEMBIC_CFG))
    command.upgrade(cfg, "head")
    command.current(cfg)


if __name__ == "__main__":
    upgrade_to_head()
