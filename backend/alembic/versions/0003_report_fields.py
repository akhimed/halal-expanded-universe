"""add report fields

Revision ID: 0003_report_fields
Revises: 0002_user_auth_fields
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_report_fields"
down_revision = "0002_user_auth_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("report_type", sa.String(length=64), nullable=True))
    op.add_column("reports", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("evidence_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "evidence_url")
    op.drop_column("reports", "description")
    op.drop_column("reports", "report_type")
