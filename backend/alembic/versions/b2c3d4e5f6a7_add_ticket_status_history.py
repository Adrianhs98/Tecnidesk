"""add_ticket_status_history

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ticket_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_ticket_status_history_id'), 'ticket_status_history', ['id'], unique=False)
    op.create_index(op.f('ix_ticket_status_history_ticket_id'), 'ticket_status_history', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_ticket_status_history_changed_at'), 'ticket_status_history', ['changed_at'], unique=False)

    # Initial backfill for existing tickets
    op.execute(
        """
        INSERT INTO ticket_status_history (id, ticket_id, from_status, to_status, changed_at, created_at)
        SELECT gen_random_uuid(), id, NULL, CAST(status AS VARCHAR(50)), created_at, created_at FROM tickets;
        """
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_ticket_status_history_changed_at'), table_name='ticket_status_history')
    op.drop_index(op.f('ix_ticket_status_history_ticket_id'), table_name='ticket_status_history')
    op.drop_index(op.f('ix_ticket_status_history_id'), table_name='ticket_status_history')
    op.drop_table('ticket_status_history')
