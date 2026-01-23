import sqlalchemy as sa
from alembic import op

revision = "6673d6fd0160"
down_revision = "6673d6fd0159"
branch_labels = None
depends_on = None
"""Add proposed_rate_type to proposals

Revision ID: 6673d6fd0160
Revises: 6673d6fd0159
Create Date: 2026-01-21
"""


def upgrade() -> None:
    op.add_column(
        "proposals",
        sa.Column("proposed_rate_type", sa.String(), nullable=False, server_default="shop"),
    )
    op.alter_column("proposals", "proposed_rate_type", server_default=None)


def downgrade() -> None:
    op.drop_column("proposals", "proposed_rate_type")
