"""Unit tests for the Admin Assistant (Ohm) service, router, and intent catalog."""
import uuid
import datetime
from datetime import timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from app.core.dependencies import admin_guard
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.user import User, UserRoleEnum
from app.schemas.admin_assistant import AdminAssistantQueryRequest, AdminAssistantQueryResponse
from app.services import admin_assistant_service
from app.routers.admin_assistant import query_admin_assistant


@pytest.mark.asyncio
async def test_classify_direct_intents():
    # 1. Ganancias del día
    assert admin_assistant_service._match_direct_intent("Ganancias de hoy") == admin_assistant_service.INTENT_GANANCIAS_DEL_DIA
    assert admin_assistant_service._match_direct_intent("cuánto hemos ganado hoy?") == admin_assistant_service.INTENT_GANANCIAS_DEL_DIA
    assert admin_assistant_service._match_direct_intent("ingresos de hoy") == admin_assistant_service.INTENT_GANANCIAS_DEL_DIA

    # 2. Equipos ingresados hoy
    assert admin_assistant_service._match_direct_intent("Equipos ingresados hoy") == admin_assistant_service.INTENT_EQUIPOS_INGRESADOS_HOY
    assert admin_assistant_service._match_direct_intent("cuántos equipos entraron hoy") == admin_assistant_service.INTENT_EQUIPOS_INGRESADOS_HOY
    assert admin_assistant_service._match_direct_intent("órdenes de hoy") == admin_assistant_service.INTENT_EQUIPOS_INGRESADOS_HOY

    # 3. Equipos sin tocar
    assert admin_assistant_service._match_direct_intent("Equipos sin tocar") == admin_assistant_service.INTENT_EQUIPOS_SIN_TOCAR
    assert admin_assistant_service._match_direct_intent("tickets sin tocar") == admin_assistant_service.INTENT_EQUIPOS_SIN_TOCAR
    assert admin_assistant_service._match_direct_intent("equipos varados") == admin_assistant_service.INTENT_EQUIPOS_SIN_TOCAR


@pytest.mark.asyncio
async def test_classify_intent_none():
    assert admin_assistant_service._match_direct_intent("Hola cómo estás") is None
    assert admin_assistant_service._match_direct_intent("Receta para hacer pizza") is None
    assert admin_assistant_service._match_direct_intent("Cuál es la capital de Ecuador?") is None


@pytest.mark.asyncio
async def test_classify_intent_llm_fallback():
    with patch("app.services.admin_assistant_service.get_settings") as mock_settings:
        mock_settings.return_value.gemini_api_key = "fake-key"
        mock_settings.return_value.gemini_fast_model = "gemini-3.5-flash-lite"

        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "ganancias_del_dia"
            mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            intent = await admin_assistant_service.classify_intent("Dame el balance financiero del taller en la jornada")
            assert intent == admin_assistant_service.INTENT_GANANCIAS_DEL_DIA


@pytest.mark.asyncio
async def test_handle_admin_query_canned_fallback():
    db = AsyncMock()
    shop_id = uuid.uuid4()

    reply, intent, data = await admin_assistant_service.handle_admin_query(
        db=db,
        shop_id=shop_id,
        message="¿Cómo está el clima hoy?",
    )

    assert intent is None
    assert data is None
    assert "Actualmente puedo asistirte con las siguientes consultas" in reply
    assert "Ganancias del día" in reply
    # Verify DB was never queried
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_handle_admin_query_revenue():
    db = AsyncMock()
    shop_id = uuid.uuid4()

    row_mock = MagicMock()
    row_mock.total_revenue = 245.50
    row_mock.completed_count = 3
    result_mock = MagicMock()
    result_mock.one.return_value = row_mock
    db.execute.return_value = result_mock

    reply, intent, data = await admin_assistant_service.handle_admin_query(
        db=db,
        shop_id=shop_id,
        message="Ganancias de hoy",
    )

    assert intent == admin_assistant_service.INTENT_GANANCIAS_DEL_DIA
    assert data["total_revenue"] == 245.50
    assert data["completed_count"] == 3
    assert "245.5" in reply
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_handle_admin_query_daily_intake():
    db = AsyncMock()
    shop_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one.return_value = 7
    db.execute.return_value = result_mock

    reply, intent, data = await admin_assistant_service.handle_admin_query(
        db=db,
        shop_id=shop_id,
        message="Equipos ingresados hoy",
    )

    assert intent == admin_assistant_service.INTENT_EQUIPOS_INGRESADOS_HOY
    assert data["intake_count"] == 7
    assert "7" in reply
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_handle_admin_query_untouched():
    db = AsyncMock()
    shop_id = uuid.uuid4()

    ticket_row = MagicMock()
    ticket_row.id = uuid.uuid4()
    ticket_row.device_brand = "Apple"
    ticket_row.device_model = "iPhone 12"
    ticket_row.status = TicketStatusEnum.EN_REVISION
    ticket_row.updated_at = datetime.datetime.now(timezone.utc) - datetime.timedelta(hours=60)

    result_mock = MagicMock()
    result_mock.all.return_value = [ticket_row]
    db.execute.return_value = result_mock

    reply, intent, data = await admin_assistant_service.handle_admin_query(
        db=db,
        shop_id=shop_id,
        message="Equipos sin tocar",
    )

    assert intent == admin_assistant_service.INTENT_EQUIPOS_SIN_TOCAR
    assert data["stale_count"] == 1
    assert "1" in reply
    assert "iPhone 12" in reply
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_admin_guard_rejection_for_technicians():
    shop_id = uuid.uuid4()
    tech_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await admin_guard(current_user=tech_user)

    assert exc_info.value.status_code == 403
    assert "Se requiere rol de administrador" in exc_info.value.detail


@pytest.mark.asyncio
async def test_admin_guard_allows_admin():
    shop_id = uuid.uuid4()
    admin_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        is_active=True,
    )

    result = await admin_guard(current_user=admin_user)
    assert result == admin_user


@pytest.mark.asyncio
async def test_router_query_endpoint():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    admin_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        is_active=True,
    )

    payload = AdminAssistantQueryRequest(message="Ganancias de hoy")

    with patch("app.services.admin_assistant_service.handle_admin_query", new_callable=AsyncMock) as mock_handle:
        mock_handle.return_value = (
            "Hoy se han recaudado $120.00 USD.",
            "ganancias_del_dia",
            {"total_revenue": 120.0, "completed_count": 2},
        )

        res = await query_admin_assistant(
            payload=payload,
            current_user=admin_user,
            db=db,
        )

        assert isinstance(res, AdminAssistantQueryResponse)
        assert res.intent == "ganancias_del_dia"
        assert "$120.00 USD" in res.reply
        mock_handle.assert_called_once_with(
            db=db,
            shop_id=shop_id,
            message="Ganancias de hoy",
        )
