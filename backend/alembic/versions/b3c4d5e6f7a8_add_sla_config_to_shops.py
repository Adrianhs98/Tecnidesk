"""add_sla_config_to_shops

Revision ID: b3c4d5e6f7a8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-22 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'shops',
        sa.Column('sla_config', sa.JSON(), nullable=True, server_default='{}')
    )


def downgrade() -> None:
    op.drop_column('shops', 'sla_config')
