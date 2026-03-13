"""add trust evidence records

Revision ID: 0005_trust_evid
Revises: 0004_verif_trust
Create Date: 2026-03-13
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_trust_evid"
down_revision = "0004_verif_trust"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trust_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurant_id", sa.Integer(), sa.ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_key", sa.String(length=64), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("stance", sa.String(length=16), nullable=False, server_default="supports"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("source_label", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence_weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trust_evidence")
