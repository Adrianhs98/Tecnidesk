"""
Plantilla para scripts de migración Alembic.
Este archivo es usado por Alembic para generar nuevos archivos de versión.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7aff55c099f7'
down_revision = 'd0c08a175bbd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Explicitly create the ENUM type first for PostgreSQL
    item_type_enum = postgresql.ENUM('part', 'labor', 'other', name='item_type_enum')
    item_type_enum.create(op.get_bind())
    
    # Add column with a server_default so existing rows don't violate non-null constraint
    op.add_column('ticket_items', sa.Column('item_type', item_type_enum, nullable=False, server_default='part'))
    # Remove the server_default to match the model definition
    op.alter_column('ticket_items', 'item_type', server_default=None)

def downgrade() -> None:
    op.drop_column('ticket_items', 'item_type')
    
    # Explicitly drop the ENUM type
    item_type_enum = postgresql.ENUM('part', 'labor', 'other', name='item_type_enum')
    item_type_enum.drop(op.get_bind())
