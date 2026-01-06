"""Initial schema with SQLAlchemy 2.0 support

Revision ID: v0_2_0
Revises:
Create Date: 2026-01-06
App Version: 0.2.0
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
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("point_value_eur", sa.Float(), server_default="0", nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), server_default="viewer", nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "shop_main",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canonical_name", sa.String(), nullable=False),
        sa.Column("canonical_name_lower", sa.String(), nullable=False),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("merged_into_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["merged_into_id"], ["shop_main.id"]),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_main_canonical_name", "shop_main", ["canonical_name"], unique=False)
    op.create_index(
        "ix_shop_main_canonical_name_lower", "shop_main", ["canonical_name_lower"], unique=False
    )

    op.create_table(
        "scrape_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shops",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("shop_main_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["shop_main_id"], ["shop_main.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shop_variants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shop_main_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("confidence_score", sa.Float(), server_default="100", nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["shop_main_id"], ["shop_main.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_id", name="unique_source_variant"),
    )

    op.create_table(
        "shop_program_rates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shop_id", sa.Integer(), nullable=False),
        sa.Column("program_id", sa.Integer(), nullable=False),
        sa.Column("points_per_eur", sa.Float(), server_default="0", nullable=True),
        sa.Column("cashback_pct", sa.Float(), server_default="0", nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("valid_to", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["bonus_programs.id"]),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("coupon_type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("shop_id", sa.Integer(), nullable=True),
        sa.Column("program_id", sa.Integer(), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("combinable", sa.Boolean(), nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("valid_to", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["program_id"], ["bonus_programs.id"]),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contributor_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("decision_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("decision_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["decision_by_admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "proposals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("source", sa.String(), server_default="user", nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("shop_id", sa.Integer(), nullable=True),
        sa.Column("program_id", sa.Integer(), nullable=True),
        sa.Column("proposed_points_per_eur", sa.Float(), nullable=True),
        sa.Column("proposed_cashback_pct", sa.Float(), nullable=True),
        sa.Column("proposed_name", sa.String(), nullable=True),
        sa.Column("proposed_point_value_eur", sa.Float(), nullable=True),
        sa.Column("proposed_coupon_type", sa.String(), nullable=True),
        sa.Column("proposed_coupon_value", sa.Float(), nullable=True),
        sa.Column("proposed_coupon_description", sa.String(), nullable=True),
        sa.Column("proposed_coupon_combinable", sa.Boolean(), nullable=True),
        sa.Column("proposed_coupon_valid_to", sa.DateTime(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by_system", sa.Boolean(), server_default="0", nullable=True),
        sa.ForeignKeyConstraint(["program_id"], ["bonus_programs.id"]),
        sa.ForeignKeyConstraint(["shop_id"], ["shops.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("link_type", sa.String(), nullable=True),
        sa.Column("link_id", sa.Integer(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "proposal_votes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("voter_id", sa.Integer(), nullable=False),
        sa.Column("vote", sa.Integer(), nullable=False),
        sa.Column("vote_weight", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"]),
        sa.ForeignKeyConstraint(["voter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("proposal_id", "voter_id", name="unique_proposal_voter"),
    )

    op.create_table(
        "shop_merge_proposals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("variant_a_id", sa.Integer(), nullable=False),
        sa.Column("variant_b_id", sa.Integer(), nullable=False),
        sa.Column("proposed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), server_default="PENDING", nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decided_reason", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["proposed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["variant_a_id"], ["shop_variants.id"]),
        sa.ForeignKeyConstraint(["variant_b_id"], ["shop_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shop_metadata_proposals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("shop_main_id", sa.String(length=36), nullable=False),
        sa.Column("proposed_name", sa.String(), nullable=True),
        sa.Column("proposed_website", sa.String(), nullable=True),
        sa.Column("proposed_logo_url", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("proposed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), server_default="PENDING", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by_user_id", sa.Integer(), nullable=True),
        sa.Column("decided_reason", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["proposed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["shop_main_id"], ["shop_main.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "rate_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("rate_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_id", sa.Integer(), nullable=False),
        sa.Column("comment_type", sa.String(), nullable=False),
        sa.Column("comment_text", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["rate_id"], ["shop_program_rates.id"]),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "proposal_audit_trails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proposal_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("details", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["proposal_id"], ["proposals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("proposal_audit_trails")
    op.drop_table("rate_comments")
    op.drop_table("shop_metadata_proposals")
    op.drop_table("shop_merge_proposals")
    op.drop_table("proposal_votes")
    op.drop_table("notifications")
    op.drop_table("proposals")
    op.drop_table("contributor_requests")
    op.drop_table("coupons")
    op.drop_table("shop_program_rates")
    op.drop_table("shop_variants")
    op.drop_table("shops")
    op.drop_table("scrape_logs")
    op.drop_index("ix_shop_main_canonical_name_lower", table_name="shop_main")
    op.drop_index("ix_shop_main_canonical_name", table_name="shop_main")
    op.drop_table("shop_main")
    op.drop_table("users")
    op.drop_table("bonus_programs")
