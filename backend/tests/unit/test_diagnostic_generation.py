import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.models.ticket import Ticket, TicketStatusEnum
from app.models.diagnostic import DiagnosticConversation, DiagnosticMessage
from app.schemas.ticket import ApplyDiagnosticRequest
from app.services.correction_service import CorrectionService


@pytest.mark.asyncio
async def test_generate_diagnostic_empty_history_raises_400():
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        device_brand="Samsung",
        device_model="A52",
        issue_description="No enciende",
        draft_diagnostic=None,
    )

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    db.execute.return_value = result_mock

    with pytest.raises(HTTPException) as exc_info:
        await CorrectionService.generate_final_diagnostic(db, ticket)

    assert exc_info.value.status_code == 400
    assert "No hay conversación previa" in exc_info.value.detail
    assert ticket.draft_diagnostic is None


@pytest.mark.asyncio
async def test_generate_diagnostic_success():
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        device_brand="Samsung",
        device_model="A52",
        issue_description="No enciende",
        draft_diagnostic=None,
    )

    conv = DiagnosticConversation(
        id=uuid.uuid4(),
        ticket_id=ticket.id,
        shop_id=ticket.shop_id,
        technician_id=uuid.uuid4(),
        status="open"
    )
    msg1 = DiagnosticMessage(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="technician",
        content="Revisé la batería, tiene 0V.",
        created_at=datetime.now(timezone.utc)
    )
    msg2 = DiagnosticMessage(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="assistant",
        content="Reemplaza la batería y prueba el ciclo de carga.",
        created_at=datetime.now(timezone.utc)
    )

    conv_res = MagicMock()
    conv_res.scalars.return_value.all.return_value = [conv]
    msg_res = MagicMock()
    msg_res.scalars.return_value.all.return_value = [msg1, msg2]

    db.execute.side_effect = [conv_res, msg_res]

    fake_ai_response = MagicMock()
    fake_ai_response.text = "Se diagnosticó batería agotada en 0V. Se realizó el cambio de batería."

    with patch("app.services.correction_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(return_value=fake_ai_response)
        mock_client_cls.return_value = mock_client

        result = await CorrectionService.generate_final_diagnostic(db, ticket)

    assert result == fake_ai_response.text
    assert ticket.draft_diagnostic == fake_ai_response.text
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_generate_diagnostic_gemini_503_raises_503_and_leaves_draft_none():
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Falla táctil",
        draft_diagnostic=None,
    )

    conv = DiagnosticConversation(id=uuid.uuid4(), ticket_id=ticket.id, shop_id=ticket.shop_id)
    msg = DiagnosticMessage(id=uuid.uuid4(), conversation_id=conv.id, role="technician", content="Medí líneas I2C")

    conv_res = MagicMock()
    conv_res.scalars.return_value.all.return_value = [conv]
    msg_res = MagicMock()
    msg_res.scalars.return_value.all.return_value = [msg]

    db.execute.side_effect = [conv_res, msg_res]

    with patch("app.services.correction_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        from google.genai import errors
        import json
        import requests
        resp = requests.Response()
        resp.status_code = 503
        resp._content = json.dumps({"error": {"code": 503, "message": "High demand"}}).encode("utf-8")
        api_err = errors.APIError(503, resp)
        api_err.code = 503
        mock_client.aio.models.generate_content = AsyncMock(side_effect=api_err)
        mock_client_cls.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await CorrectionService.generate_final_diagnostic(db, ticket)

    assert exc_info.value.status_code == 503
    assert ticket.draft_diagnostic is None
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_apply_diagnostic_without_draft_raises_400():
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        device_brand="Xiaomi",
        device_model="Redmi Note 11",
        issue_description="No carga",
        draft_diagnostic=None,
        diagnostic_notes=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await CorrectionService.apply_final_diagnostic(db, ticket, edited_diagnostic=None)

    assert exc_info.value.status_code == 400
    assert "No hay un diagnóstico generado" in exc_info.value.detail
    db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_apply_diagnostic_without_manual_edit():
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        device_brand="Xiaomi",
        device_model="Redmi Note 11",
        issue_description="No carga",
        draft_diagnostic="Diagnóstico original de Ohm.",
        diagnostic_notes=None,
        diagnostic_applied_at=None,
    )

    updated = await CorrectionService.apply_final_diagnostic(db, ticket, edited_diagnostic=None)

    assert updated.diagnostic_notes == "Diagnóstico original de Ohm."
    assert updated.draft_diagnostic == "Diagnóstico original de Ohm."
    assert updated.diagnostic_applied_at is not None
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_apply_diagnostic_with_manual_edit():
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        device_brand="Xiaomi",
        device_model="Redmi Note 11",
        issue_description="No carga",
        draft_diagnostic="Diagnóstico original de Ohm.",
        diagnostic_notes=None,
        diagnostic_applied_at=None,
    )

    updated = await CorrectionService.apply_final_diagnostic(
        db, ticket, edited_diagnostic="   Diagnóstico editado por el técnico.   "
    )

    assert updated.diagnostic_notes == "Diagnóstico editado por el técnico."
    assert updated.draft_diagnostic == "Diagnóstico editado por el técnico."
    assert updated.diagnostic_applied_at is not None
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_router_generate_diagnostic_status_gating_raises_400():
    from app.routers.tickets import generate_diagnostic
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REVISION,
        draft_diagnostic=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        await generate_diagnostic(ticket_id=ticket.id, ticket=ticket, db=db)

    assert exc_info.value.status_code == 400
    assert "solo está permitida en reparación o listo para entrega" in exc_info.value.detail


@pytest.mark.asyncio
async def test_router_generate_diagnostic_already_exists_raises_409():
    from app.routers.tickets import generate_diagnostic
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        draft_diagnostic="Diagnóstico previo ya existente",
    )

    with pytest.raises(HTTPException) as exc_info:
        await generate_diagnostic(ticket_id=ticket.id, ticket=ticket, db=db)

    assert exc_info.value.status_code == 409
    assert "Ya se generó un diagnóstico para este ticket" in exc_info.value.detail


@pytest.mark.asyncio
async def test_router_generate_diagnostic_success():
    from app.routers.tickets import generate_diagnostic
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        draft_diagnostic=None,
    )

    with patch.object(CorrectionService, "generate_final_diagnostic", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Diagnóstico generado correctamente."
        res = await generate_diagnostic(ticket_id=ticket.id, ticket=ticket, db=db)

    assert res.draft_diagnostic == "Diagnóstico generado correctamente."
    mock_gen.assert_awaited_once_with(db=db, ticket=ticket)


@pytest.mark.asyncio
async def test_router_apply_diagnostic_success():
    from app.routers.tickets import apply_diagnostic
    db = AsyncMock()
    ticket = Ticket(
        id=uuid.uuid4(),
        shop_id=uuid.uuid4(),
        status=TicketStatusEnum.EN_REPARACION,
        draft_diagnostic="Borrador previo",
    )
    payload = ApplyDiagnosticRequest(edited_diagnostic="Versión final corregida")

    with patch.object(CorrectionService, "apply_final_diagnostic", new_callable=AsyncMock) as mock_apply:
        mock_apply.return_value = ticket
        res = await apply_diagnostic(ticket_id=ticket.id, payload=payload, ticket=ticket, db=db)

    assert res == ticket
    mock_apply.assert_awaited_once_with(db=db, ticket=ticket, edited_diagnostic="Versión final corregida")

