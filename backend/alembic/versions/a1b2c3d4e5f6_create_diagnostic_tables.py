"""create_diagnostic_tables

Revision ID: a1b2c3d4e5f6
Revises: eced82f75a94
Create Date: 2026-08-20 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'eced82f75a94'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;")

    # 2. Diagnostic Cases (Synthetic benchmarks + Real workshop outcomes)
    op.create_table(
        'diagnostic_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('shop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shops.id', ondelete='CASCADE'), nullable=True),
        sa.Column('origin_ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('derived_from_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('diagnostic_cases.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('device_brand', sa.String(length=100), nullable=False),
        sa.Column('device_model', sa.String(length=100), nullable=False),
        sa.Column('symptom_text', sa.Text(), nullable=False),
        sa.Column('diagnosed_cause', sa.Text(), nullable=False),
        sa.Column('solution_applied', sa.Text(), nullable=False),
        sa.Column('repair_time_minutes', sa.Integer(), nullable=True),
        sa.Column('estimated_cost', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("source_type IN ('synthetic', 'real_validated')", name='ck_diagnostic_cases_source_type'),
    )
    op.create_index(op.f('ix_diagnostic_cases_id'), 'diagnostic_cases', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_cases_shop_id'), 'diagnostic_cases', ['shop_id'], unique=False)
    op.create_index('ix_diagnostic_cases_shop_brand_model', 'diagnostic_cases', ['shop_id', 'device_brand', 'device_model'], unique=False)
    
    # HNSW Cosine Distance Index
    op.execute(
        "CREATE INDEX ix_diagnostic_cases_embedding_hnsw "
        "ON diagnostic_cases USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64);"
    )

    # 3. Diagnostic Conversations (Human-in-the-loop chat threads)
    op.create_table(
        'diagnostic_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('diagnostic_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('diagnostic_cases.id', ondelete='CASCADE'), nullable=True),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('technician_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('technicians.id'), nullable=False),
        sa.Column('shop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shops.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='open', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('open', 'confirmed', 'corrected', 'abandoned')", name='ck_diagnostic_conversations_status'),
    )
    op.create_index(op.f('ix_diagnostic_conversations_id'), 'diagnostic_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_conversations_ticket_id'), 'diagnostic_conversations', ['ticket_id'], unique=False)
    op.create_index(op.f('ix_diagnostic_conversations_shop_id'), 'diagnostic_conversations', ['shop_id'], unique=False)

    # 4. Diagnostic Messages (Chat history)
    op.create_table(
        'diagnostic_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('diagnostic_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("role IN ('system', 'technician', 'assistant')", name='ck_diagnostic_messages_role'),
    )
    op.create_index(op.f('ix_diagnostic_messages_id'), 'diagnostic_messages', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_messages_conversation_id'), 'diagnostic_messages', ['conversation_id'], unique=False)

    # 5. Diagnostic Query Log (Telemetry & Maturity Metric)
    op.create_table(
        'diagnostic_query_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('shop_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('shops.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tickets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('top_case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('diagnostic_cases.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_type_used', sa.String(length=20), nullable=True),
        sa.Column('similarity_score', sa.Float(), nullable=True),
        sa.Column('had_sufficient_evidence', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_diagnostic_query_log_id'), 'diagnostic_query_log', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_query_log_shop_id'), 'diagnostic_query_log', ['shop_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_diagnostic_query_log_shop_id'), table_name='diagnostic_query_log')
    op.drop_index(op.f('ix_diagnostic_query_log_id'), table_name='diagnostic_query_log')
    op.drop_table('diagnostic_query_log')

    op.drop_index(op.f('ix_diagnostic_messages_conversation_id'), table_name='diagnostic_messages')
    op.drop_index(op.f('ix_diagnostic_messages_id'), table_name='diagnostic_messages')
    op.drop_table('diagnostic_messages')

    op.drop_index(op.f('ix_diagnostic_conversations_shop_id'), table_name='diagnostic_conversations')
    op.drop_index(op.f('ix_diagnostic_conversations_ticket_id'), table_name='diagnostic_conversations')
    op.drop_index(op.f('ix_diagnostic_conversations_id'), table_name='diagnostic_conversations')
    op.drop_table('diagnostic_conversations')

    op.drop_index('ix_diagnostic_cases_shop_brand_model', table_name='diagnostic_cases')
    op.execute("DROP INDEX IF EXISTS ix_diagnostic_cases_embedding_hnsw;")
    op.drop_index(op.f('ix_diagnostic_cases_shop_id'), table_name='diagnostic_cases')
    op.drop_index(op.f('ix_diagnostic_cases_id'), table_name='diagnostic_cases')
    op.drop_table('diagnostic_cases')
