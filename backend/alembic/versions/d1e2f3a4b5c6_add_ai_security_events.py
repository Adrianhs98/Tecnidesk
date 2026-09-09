"""add_ai_security_events

Revision ID: d1e2f3a4b5c6
Revises: f6a7b8c9d0e1
Create Date: 2026-09-08 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ai_security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('shop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shops.id', ondelete='CASCADE'), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('technicians.id', ondelete='SET NULL'), nullable=True),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False, server_default='injection_attempt'),
        sa.Column('message_excerpt', sa.String(length=280), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_ai_security_events_id', 'ai_security_events', ['id'], unique=False)
    op.create_index('ix_ai_security_events_shop_id', 'ai_security_events', ['shop_id'], unique=False)
    op.create_index('ix_ai_security_events_technician_id', 'ai_security_events', ['technician_id'], unique=False)
    op.create_index('ix_ai_security_events_ticket_id', 'ai_security_events', ['ticket_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ai_security_events_ticket_id', table_name='ai_security_events')
    op.drop_index('ix_ai_security_events_technician_id', table_name='ai_security_events')
    op.drop_index('ix_ai_security_events_shop_id', table_name='ai_security_events')
    op.drop_index('ix_ai_security_events_id', table_name='ai_security_events')
    op.drop_table('ai_security_events')
