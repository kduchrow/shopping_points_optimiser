"""add scheduled job runs table

Revision ID: v0_2_2
Revises: v0_2_1
Create Date: 2026-01-07 09:35:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "v0_2_2"
down_revision = "v0_2_1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "scheduled_job_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scheduled_job_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["scheduled_job_id"], ["scheduled_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_scheduled_job_runs_scheduled_job_id"),
        "scheduled_job_runs",
        ["scheduled_job_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_scheduled_job_runs_scheduled_job_id"), table_name="scheduled_job_runs")
    op.drop_table("scheduled_job_runs")
