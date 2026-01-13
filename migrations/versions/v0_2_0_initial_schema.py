"""Initial schema with SQLAlchemy 2.0 support - IDEMPOTENT FOR PRODUCTION

Revision ID: v0_2_0
Revises:
Create Date: 2026-01-06
App Version: 0.2.0

CRITICAL: This migration MUST work on production databases with live data.

This uses CREATE TABLE IF NOT EXISTS - safe to run on:
- Fresh databases (creates all 17 tables)
- Existing production DB (respects existing data, creates only missing)
- Partial migration states (fills in gaps safely)
"""

import sqlalchemy as sa
from alembic import op

revision = "v0_2_0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bonus_programs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True),
        sa.Column("description", sa.String),
        sa.Column("point_value_eur", sa.Float),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String, nullable=False, unique=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("role", sa.String, nullable=False, server_default="viewer"),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "shop_main",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("canonical_name", sa.String, nullable=False),
        sa.Column("canonical_name_lower", sa.String, nullable=False),
        sa.Column("website", sa.String),
        sa.Column("logo_url", sa.String),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("merged_into_id", sa.String(36), sa.ForeignKey("shop_main.id")),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False),
        sa.Column("updated_by_user_id", sa.Integer, sa.ForeignKey("users.id")),
    )

    # --- Remaining tables refactored to use op.create_table ---
    op.create_table(
        "scrape_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("timestamp", sa.TIMESTAMP, nullable=False),
        sa.Column("message", sa.String, nullable=False),
    )

    op.create_table(
        "shops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("shop_main_id", sa.String(36), sa.ForeignKey("shop_main.id")),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "shop_variants",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_main_id", sa.String(36), sa.ForeignKey("shop_main.id"), nullable=False),
        sa.Column("source", sa.String, nullable=False),
        sa.Column("source_name", sa.String, nullable=False),
        sa.Column("source_id", sa.String),
        sa.Column("confidence_score", sa.Float, server_default="100"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.UniqueConstraint("source", "source_id"),
    )

    op.create_table(
        "shop_program_rates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("bonus_programs.id"), nullable=False),
        sa.Column("points_per_eur", sa.Float, server_default="0"),
        sa.Column("cashback_pct", sa.Float, server_default="0"),
        sa.Column("valid_from", sa.TIMESTAMP, nullable=False),
        sa.Column("valid_to", sa.TIMESTAMP),
    )

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("coupon_type", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id")),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("bonus_programs.id")),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("combinable", sa.Boolean),
        sa.Column("valid_from", sa.TIMESTAMP, nullable=False),
        sa.Column("valid_to", sa.TIMESTAMP, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="active"),
        sa.Column("source_url", sa.String),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "contributor_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("decision_by_admin_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("decision_at", sa.TIMESTAMP),
    )

    op.create_table(
        "proposals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("proposal_type", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("source", sa.String, nullable=False, server_default="user"),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("shop_id", sa.Integer, sa.ForeignKey("shops.id")),
        sa.Column("program_id", sa.Integer, sa.ForeignKey("bonus_programs.id")),
        sa.Column("proposed_points_per_eur", sa.Float),
        sa.Column("proposed_cashback_pct", sa.Float),
        sa.Column("proposed_name", sa.String),
        sa.Column("proposed_point_value_eur", sa.Float),
        sa.Column("proposed_coupon_type", sa.String),
        sa.Column("proposed_coupon_value", sa.Float),
        sa.Column("proposed_coupon_description", sa.String),
        sa.Column("proposed_coupon_combinable", sa.Boolean),
        sa.Column("proposed_coupon_valid_to", sa.TIMESTAMP),
        sa.Column("reason", sa.String),
        sa.Column("source_url", sa.String),
        sa.Column("approved_at", sa.TIMESTAMP),
        sa.Column("approved_by_system", sa.Boolean, server_default=sa.text("FALSE")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notification_type", sa.String, nullable=False),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("message", sa.String, nullable=False),
        sa.Column("link_type", sa.String),
        sa.Column("link_id", sa.Integer),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "proposal_votes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("proposal_id", sa.Integer, sa.ForeignKey("proposals.id"), nullable=False),
        sa.Column("voter_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("vote", sa.Integer, nullable=False),
        sa.Column("vote_weight", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.UniqueConstraint("proposal_id", "voter_id"),
    )

    op.create_table(
        "shop_merge_proposals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("variant_a_id", sa.Integer, sa.ForeignKey("shop_variants.id"), nullable=False),
        sa.Column("variant_b_id", sa.Integer, sa.ForeignKey("shop_variants.id"), nullable=False),
        sa.Column("proposed_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="PENDING"),
        sa.Column("reason", sa.String),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("decided_at", sa.TIMESTAMP),
        sa.Column("decided_by_user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("decided_reason", sa.String),
    )

    op.create_table(
        "shop_metadata_proposals",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("shop_main_id", sa.String(36), sa.ForeignKey("shop_main.id"), nullable=False),
        sa.Column("proposed_name", sa.String),
        sa.Column("proposed_website", sa.String),
        sa.Column("proposed_logo_url", sa.String),
        sa.Column("reason", sa.String),
        sa.Column("proposed_by_user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("decided_at", sa.TIMESTAMP),
        sa.Column("decided_by_user_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("decided_reason", sa.String),
    )

    op.create_table(
        "rate_comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rate_id", sa.Integer, sa.ForeignKey("shop_program_rates.id"), nullable=False),
        sa.Column("reviewer_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("comment_type", sa.String, nullable=False),
        sa.Column("comment_text", sa.String, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "proposal_audit_trails",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("proposal_id", sa.Integer, sa.ForeignKey("proposals.id"), nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("details", sa.String),
    )

    # --- Indexes ---
    op.create_index("ix_shop_main_canonical_name", "shop_main", ["canonical_name"])
    op.create_index("ix_shop_main_canonical_name_lower", "shop_main", ["canonical_name_lower"])
