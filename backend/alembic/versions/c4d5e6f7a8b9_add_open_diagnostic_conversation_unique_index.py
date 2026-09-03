"""Enforce one open diagnostic conversation per technician ticket context.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-08-26 00:00:00.000000
"""
from alembic import op


revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the earliest open thread and close accidental duplicates before the
    # partial unique index is installed on existing workshops.
    op.execute("""
        WITH ranked AS (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY shop_id, technician_id, ticket_id
                       ORDER BY created_at, id
                   ) AS position
            FROM diagnostic_conversations
            WHERE status = 'open'
        )
        UPDATE diagnostic_conversations AS conversations
        SET status = 'abandoned', closed_at = CURRENT_TIMESTAMP
        FROM ranked
        WHERE conversations.id = ranked.id AND ranked.position > 1
    """)
    op.create_index(
        "uq_diagnostic_conversations_open_context",
        "diagnostic_conversations",
        ["shop_id", "technician_id", "ticket_id"],
        unique=True,
        postgresql_where="status = 'open'",
    )


def downgrade() -> None:
    op.drop_index("uq_diagnostic_conversations_open_context", table_name="diagnostic_conversations")
