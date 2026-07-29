"""add_sku_to_inventory

Scoped migration: adds optional SKU column to inventory for server-side search.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'eced82f75a94'
down_revision = '1dacdd1b27be'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Scoped to this change only: add sku column to inventory
    op.add_column('inventory', sa.Column('sku', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_inventory_sku'), 'inventory', ['sku'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_sku'), table_name='inventory')
    op.drop_column('inventory', 'sku')
