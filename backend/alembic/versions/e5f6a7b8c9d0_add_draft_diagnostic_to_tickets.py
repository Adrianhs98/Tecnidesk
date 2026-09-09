"""add_draft_diagnostic_to_tickets

Revision ID: e5f6a7b8c9d0
Revises: c4d5e6f7a8b9
Create Date: 2026-09-07 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f6a7b8c9d0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'tickets',
        sa.Column('draft_diagnostic', sa.Text(), nullable=True)
    )
    op.add_column(
        'tickets',
        sa.Column('diagnostic_applied_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('tickets', 'diagnostic_applied_at')
    op.drop_column('tickets', 'draft_diagnostic')
