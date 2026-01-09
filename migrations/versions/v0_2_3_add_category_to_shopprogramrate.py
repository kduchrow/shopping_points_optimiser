import sqlalchemy as sa
from alembic import op

revision = "v0_2_3"
down_revision = "v0_2_2"
branch_labels = None
depends_on = None
"""Bump version to v0.2.3: Add shop_categories and category_id to ShopProgramRate

Revision ID: v0_2_3
Revises: v0_2_2
Create Date: 2026-01-08
"""


def upgrade():
    # Create shop_categories table for normalized categories
    op.create_table(
        "shop_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("shop_categories.id"), nullable=True),
    )

    # Add nullable category_id column to shop_program_rates for normalized relation
    op.add_column("shop_program_rates", sa.Column("category_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_shop_program_rates_category_id",
        "shop_program_rates",
        "shop_categories",
        ["category_id"],
        ["id"],
    )

    # Migrate legacy free-text `category` values into shop_categories and set category_id
    conn = op.get_bind()
    res = conn.execute(
        sa.text(
            "SELECT DISTINCT category FROM shop_program_rates WHERE category IS NOT NULL AND category <> ''"
        )
    )
    categories = [row[0] for row in res]
    for name in categories:
        # Insert or ignore existing
        insert_sql = sa.text(
            "INSERT INTO shop_categories (name) VALUES (:name) ON CONFLICT (name) DO NOTHING RETURNING id"
        )
        r = conn.execute(insert_sql, {"name": name})
        row = r.fetchone()
        if row and row[0]:
            cid = row[0]
        else:
            sel = conn.execute(
                sa.text("SELECT id FROM shop_categories WHERE name = :name"), {"name": name}
            ).fetchone()
            cid = sel[0] if sel else None
        if cid:
            conn.execute(
                sa.text("UPDATE shop_program_rates SET category_id = :cid WHERE category = :name"),
                {"cid": cid, "name": name},
            )

    # Drop legacy column if it exists
    insp = sa.inspect(conn)
    columns = [col["name"] for col in insp.get_columns("shop_program_rates")]
    if "category" in columns:
        try:
            op.drop_column("shop_program_rates", "category")
        except Exception:
            pass


def downgrade():
    # Drop FK and column, then drop table
    # Recreate legacy free-text column and populate from category_id if possible
    try:
        op.add_column("shop_program_rates", sa.Column("category", sa.String(), nullable=True))
        conn = op.get_bind()
        res = conn.execute(sa.text("SELECT id, name FROM shop_categories"))
        mapping = {row[0]: row[1] for row in res}
        for cid, name in mapping.items():
            conn.execute(
                sa.text("UPDATE shop_program_rates SET category = :name WHERE category_id = :cid"),
                {"name": name, "cid": cid},
            )
    except Exception:
        pass

    op.drop_constraint(
        "fk_shop_program_rates_category_id", "shop_program_rates", type_="foreignkey"
    )
    op.drop_column("shop_program_rates", "category_id")
    op.drop_table("shop_categories")
