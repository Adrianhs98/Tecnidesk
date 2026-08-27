from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.diagnostic import DiagnosticConversation
from app.services.correction_service import CorrectionService


def test_open_conversation_has_partial_unique_context_index():
    index = next(
        item for item in DiagnosticConversation.__table__.indexes
        if item.name == "uq_diagnostic_conversations_open_context"
    )
    assert index.unique is True
    assert [column.name for column in index.columns] == ["shop_id", "technician_id", "ticket_id"]
    assert str(index.dialect_options["postgresql"]["where"]) == "status = 'open'"


@pytest.mark.asyncio
async def test_get_or_create_recovers_the_open_conversation_after_unique_race():
    no_conversation = MagicMock()
    no_conversation.scalar_one_or_none.return_value = None
    no_log = MagicMock()
    no_log.scalar_one_or_none.return_value = None
    existing_conversation = MagicMock(spec=DiagnosticConversation)
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[no_conversation, no_log])
    db.commit = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("duplicate")))
    db.rollback = AsyncMock()
    db.scalar = AsyncMock(return_value=existing_conversation)

    result = await CorrectionService.get_or_create_conversation(
        db,
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )

    assert result is existing_conversation
    db.rollback.assert_awaited_once()
    db.scalar.assert_awaited_once()
