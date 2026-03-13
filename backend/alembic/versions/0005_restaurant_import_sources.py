"""add restaurant import source metadata

Revision ID: 0005_import_sources
Revises: 0004_verif_trust
Create Date: 2026-03-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_import_sources"
down_revision = "0004_verif_trust"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "restaurant_import_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurant_id", sa.Integer(), sa.ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_name", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("imported_at", sa.DateTime(), nullable=False),
        sa.Column("freshness_at", sa.DateTime(), nullable=False),
        sa.Column("raw_source_payload", sa.Text(), nullable=False),
        sa.UniqueConstraint("source_name", "source_id", name="uq_restaurant_import_source"),
    )


def downgrade() -> None:
    op.drop_table("restaurant_import_sources")
