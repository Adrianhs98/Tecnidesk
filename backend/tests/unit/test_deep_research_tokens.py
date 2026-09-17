import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.schemas.diagnostic import DiagnosticMessageIn
from app.services.ai_safety_service import MessageSafetyResult
from app.services.llm_gateway import LLMResult
from app.services.correction_service import CorrectionService


@pytest.mark.asyncio
async def test_deep_research_passes_1500_max_output_tokens():
    """Confirms that deep_research=True dispatches 1500 max_output_tokens and tier='reasoning'."""
    from datetime import datetime, timezone

    async def mock_refresh(obj):
        if not getattr(obj, "id", None):
            obj.id = uuid4()
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    mock_db.add = MagicMock()

    # Mock ticket query
    mock_ticket = MagicMock()
    mock_ticket.device_brand = "Samsung"
    mock_ticket.device_model = "A52"
    mock_ticket.issue_description = "No enciende"
    mock_ticket_res = MagicMock()
    mock_ticket_res.scalar_one_or_none.return_value = mock_ticket

    # Mock messages query
    mock_messages_res = MagicMock()
    mock_messages_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [mock_messages_res, mock_ticket_res]

    mock_conv = MagicMock()
    mock_conv.id = uuid4()

    mock_safety = MessageSafetyResult(on_topic=True, injection_attempt=False)
    captured_llm_kwargs = {}

    async def mock_generate_llm_content(prompt, tier="fast", **kwargs):
        captured_llm_kwargs["tier"] = tier
        captured_llm_kwargs.update(kwargs)
        return LLMResult(
            text="Respuesta técnica completa sin corte.",
            provider="gemini",
            model_used="gemini-3.6-flash",
            is_fallback=False,
            latency_ms=50.0,
        )

    with patch.object(CorrectionService, "get_or_create_conversation", new=AsyncMock(return_value=mock_conv)), \
         patch("app.services.correction_service.classify_message_safety", new=AsyncMock(return_value=mock_safety)), \
         patch("app.services.correction_service.search_technical_web", new=AsyncMock(return_value=[])), \
         patch("app.services.correction_service.generate_llm_content", new=mock_generate_llm_content):

        response = await CorrectionService.handle_chat_message(
            db=mock_db,
            shop_id=uuid4(),
            technician_id=uuid4(),
            ticket_id=uuid4(),
            message_in=DiagnosticMessageIn(
                message="¿Cómo medir el PMIC PM6150?",
                deep_research=True,
            ),
        )

        assert captured_llm_kwargs["tier"] == "reasoning"
        assert captured_llm_kwargs["max_output_tokens"] == 1500
        assert captured_llm_kwargs["timeout_seconds"] == 22.0
        assert "Respuesta técnica completa" in response.content


@pytest.mark.asyncio
async def test_standard_fast_chat_preserves_fast_tokens_and_uses_primary_timeout():
    """Confirms that deep_research=False for fast tier uses 320 tokens and primary timeout (12.0s)."""
    from datetime import datetime, timezone

    async def mock_refresh(obj):
        if not getattr(obj, "id", None):
            obj.id = uuid4()
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    mock_db.add = MagicMock()

    mock_ticket = MagicMock()
    mock_ticket.device_brand = "Samsung"
    mock_ticket.device_model = "A52"
    mock_ticket.issue_description = "No enciende"
    mock_ticket_res = MagicMock()
    mock_ticket_res.scalar_one_or_none.return_value = mock_ticket

    mock_messages_res = MagicMock()
    mock_messages_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [mock_messages_res, mock_ticket_res]

    mock_conv = MagicMock()
    mock_conv.id = uuid4()

    mock_safety = MessageSafetyResult(on_topic=True, injection_attempt=False)
    captured_llm_kwargs = {}

    async def mock_generate_llm_content(prompt, tier="fast", **kwargs):
        captured_llm_kwargs["tier"] = tier
        captured_llm_kwargs.update(kwargs)
        return LLMResult(
            text="Respuesta estándar.",
            provider="gemini",
            model_used="gemini-3.5-flash-lite",
            is_fallback=False,
            latency_ms=25.0,
        )

    with patch.object(CorrectionService, "get_or_create_conversation", new=AsyncMock(return_value=mock_conv)), \
         patch("app.services.correction_service.classify_message_safety", new=AsyncMock(return_value=mock_safety)), \
         patch("app.services.correction_service.search_technical_web", new=AsyncMock(return_value=[])), \
         patch("app.services.correction_service.generate_llm_content", new=mock_generate_llm_content):

        response = await CorrectionService.handle_chat_message(
            db=mock_db,
            shop_id=uuid4(),
            technician_id=uuid4(),
            ticket_id=uuid4(),
            message_in=DiagnosticMessageIn(
                message="¿Qué repuesto sugieres?",
                deep_research=False,
            ),
        )

        assert captured_llm_kwargs["tier"] == "fast"
        assert captured_llm_kwargs["max_output_tokens"] == 320
        assert captured_llm_kwargs["timeout_seconds"] == 12.0


@pytest.mark.asyncio
async def test_standard_reasoning_chat_uses_1500_tokens_and_12s_timeout():
    """Confirms that deep_research=False with reasoning intent gets 1500 tokens and 12.0s timeout."""
    from datetime import datetime, timezone

    async def mock_refresh(obj):
        if not getattr(obj, "id", None):
            obj.id = uuid4()
        if not getattr(obj, "created_at", None):
            obj.created_at = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock(side_effect=mock_refresh)
    mock_db.add = MagicMock()

    mock_ticket = MagicMock()
    mock_ticket.device_brand = "Samsung"
    mock_ticket.device_model = "A52"
    mock_ticket.issue_description = "No enciende"
    mock_ticket_res = MagicMock()
    mock_ticket_res.scalar_one_or_none.return_value = mock_ticket

    mock_messages_res = MagicMock()
    mock_messages_res.scalars.return_value.all.return_value = []

    mock_db.execute.side_effect = [mock_messages_res, mock_ticket_res]

    mock_conv = MagicMock()
    mock_conv.id = uuid4()

    mock_safety = MessageSafetyResult(on_topic=True, injection_attempt=False)
    captured_llm_kwargs = {}

    async def mock_generate_llm_content(prompt, tier="fast", **kwargs):
        captured_llm_kwargs["tier"] = tier
        captured_llm_kwargs.update(kwargs)
        return LLMResult(
            text="Respuesta técnica de razonamiento.",
            provider="gemini",
            model_used="gemini-3.6-flash",
            is_fallback=False,
            latency_ms=45.0,
        )

    with patch.object(CorrectionService, "get_or_create_conversation", new=AsyncMock(return_value=mock_conv)), \
         patch("app.services.correction_service.classify_message_safety", new=AsyncMock(return_value=mock_safety)), \
         patch("app.services.correction_service.search_technical_web", new=AsyncMock(return_value=[])), \
         patch("app.services.correction_service.generate_llm_content", new=mock_generate_llm_content):

        response = await CorrectionService.handle_chat_message(
            db=mock_db,
            shop_id=uuid4(),
            technician_id=uuid4(),
            ticket_id=uuid4(),
            message_in=DiagnosticMessageIn(
                message="Ya probé varias veces y sigue igual el consumo del PMIC",
                deep_research=False,
            ),
        )

        assert captured_llm_kwargs["tier"] == "reasoning"
        assert captured_llm_kwargs["max_output_tokens"] == 1500
        assert captured_llm_kwargs["timeout_seconds"] == 12.0
        assert "Respuesta técnica de razonamiento" in response.content
