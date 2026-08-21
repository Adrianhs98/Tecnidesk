import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ticket_service import reject_ticket_by_token
from app.models.ticket import Ticket, TicketStatusEnum

@pytest.mark.asyncio
async def test_reject_ticket_with_reason():
    db_mock = AsyncMock()
    
    # Mock ticket
    ticket = Ticket()
    ticket.id = MagicMock()
    ticket.status = TicketStatusEnum.ESPERANDO_APROBACION
    ticket.internal_notes = "Original notes"
    
    # Mock database result
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = ticket
    
    refreshed_mock = MagicMock()
    refreshed_mock.scalar_one.return_value = ticket
    
    db_mock.execute.side_effect = [result_mock, refreshed_mock]
    
    updated_ticket = await reject_ticket_by_token(db_mock, "token123", rejection_reason="Too expensive")
    
    assert updated_ticket.status == TicketStatusEnum.NO_APROBADO
    assert updated_ticket.internal_notes == "[MOTIVO DE RECHAZO]: Too expensive\nOriginal notes"
    db_mock.commit.assert_called_once()

@pytest.mark.asyncio
async def test_reject_ticket_without_reason():
    db_mock = AsyncMock()
    
    ticket = Ticket()
    ticket.id = MagicMock()
    ticket.status = TicketStatusEnum.ESPERANDO_APROBACION
    ticket.internal_notes = "Original notes"
    
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = ticket
    
    refreshed_mock = MagicMock()
    refreshed_mock.scalar_one.return_value = ticket
    
    db_mock.execute.side_effect = [result_mock, refreshed_mock]
    
    updated_ticket = await reject_ticket_by_token(db_mock, "token123", rejection_reason=None)
    
    assert updated_ticket.status == TicketStatusEnum.NO_APROBADO
    assert updated_ticket.internal_notes == "Original notes"
    db_mock.commit.assert_called_once()
