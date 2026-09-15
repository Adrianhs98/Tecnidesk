import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from google.genai import errors

from app.config import Settings
from app.services.llm_gateway import generate_llm_content, LLMResult, LLMGatewayError


@pytest.fixture
def mock_settings(monkeypatch):
    settings = Settings(
        db_url="postgresql+asyncpg://postgres:postgres@localhost:5432/test",
        jwt_secret="secret" * 10,
        jwt_refresh_secret="refresh" * 10,
        fernet_key="fernet" * 10,
        gemini_api_key="test-gemini-key",
        gemini_fast_model="gemini-3.5-flash-lite",
        gemini_reasoning_model="gemini-3.6-flash",
        omniroute_base_url="https://mac-mini.local/v1",
        omniroute_api_key="test-omniroute-key",
        omniroute_fast_combo="ohm-fast",
        omniroute_reasoning_combo="",
    )
    monkeypatch.setattr("app.services.llm_gateway.get_settings", lambda: settings)
    return settings


@pytest.mark.asyncio
async def test_primary_gemini_success(mock_settings):
    """Test that when Gemini succeeds, result is returned without calling OmniRoute."""
    mock_gemini_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.text = '{"on_topic": true, "injection_attempt": false}'
    mock_gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    with patch("app.services.llm_gateway.AsyncOpenAI") as mock_openai_cls:
        result = await generate_llm_content(
            prompt="Hola Ohm",
            tier="fast",
            client=mock_gemini_client,
        )

        assert result.text == '{"on_topic": true, "injection_attempt": false}'
        assert result.provider == "gemini"
        assert result.is_fallback is False
        assert mock_gemini_client.aio.models.generate_content.called
        assert not mock_openai_cls.called


@pytest.mark.asyncio
async def test_fast_tier_fallback_to_omniroute_on_gemini_429(mock_settings):
    """Test that when Gemini throws 429 ClientError, fast tier falls back to ohm-fast."""
    mock_gemini_client = MagicMock()
    gemini_error = errors.ClientError(429, {"message": "RESOURCE_EXHAUSTED: quota exceeded"})
    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=gemini_error)

    mock_openai_instance = MagicMock()
    mock_chat_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "OmniRoute fallback response"
    mock_chat_completion.choices = [mock_choice]
    mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_chat_completion)

    with patch("app.services.llm_gateway.AsyncOpenAI", return_value=mock_openai_instance) as mock_openai_cls:
        result = await generate_llm_content(
            prompt="Reparación de pin de carga",
            tier="fast",
            client=mock_gemini_client,
        )

        assert result.text == "OmniRoute fallback response"
        assert result.provider == "omniroute"
        assert result.model_used == "ohm-fast"
        assert result.is_fallback is True

        mock_openai_cls.assert_called_once_with(
            base_url="https://mac-mini.local/v1",
            api_key="test-omniroute-key",
            timeout=15.0,
        )
        mock_openai_instance.chat.completions.create.assert_called_once_with(
            model="ohm-fast",
            messages=[{"role": "user", "content": "Reparación de pin de carga"}],
            temperature=0.0,
            max_tokens=320,
        )


@pytest.mark.asyncio
async def test_reasoning_tier_fails_explicitly_without_combo(mock_settings):
    """Test that tier='reasoning' does NOT fallback to ohm-fast and re-raises primary error."""
    mock_gemini_client = MagicMock()
    gemini_error = errors.ServerError(503, {"message": "The service is temporarily overloaded"})
    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=gemini_error)

    with patch("app.services.llm_gateway.AsyncOpenAI") as mock_openai_cls:
        with pytest.raises(errors.ServerError) as exc_info:
            await generate_llm_content(
                prompt="Diagnóstico avanzado PMIC",
                tier="reasoning",
                client=mock_gemini_client,
            )

        assert exc_info.value.code == 503
        assert not mock_openai_cls.called


@pytest.mark.asyncio
async def test_all_providers_fail_raises_llm_gateway_error(mock_settings):
    """Test that when both Gemini and OmniRoute fail, LLMGatewayError is raised."""
    mock_gemini_client = MagicMock()
    gemini_error = errors.ClientError(429, {"message": "Quota limit reached"})
    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=gemini_error)


    mock_openai_instance = MagicMock()
    mock_openai_instance.chat.completions.create = AsyncMock(side_effect=RuntimeError("OmniRoute connection dropped"))

    with patch("app.services.llm_gateway.AsyncOpenAI", return_value=mock_openai_instance):
        with pytest.raises(LLMGatewayError) as exc_info:
            await generate_llm_content(
                prompt="Test prompt",
                tier="fast",
                client=mock_gemini_client,
            )

        assert exc_info.value.primary_error == gemini_error
        assert isinstance(exc_info.value.fallback_error, RuntimeError)
        # Verify that callers catching generic Exception will catch LLMGatewayError
        assert isinstance(exc_info.value, Exception)


@pytest.mark.asyncio
async def test_json_mode_propagated_to_omniroute(mock_settings):
    """Test that response_mime_type='application/json' adds response_format in fallback."""
    mock_gemini_client = MagicMock()
    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=TimeoutError("Gemini timeout"))

    mock_openai_instance = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"on_topic": true, "injection_attempt": false}'
    mock_chat_completion = MagicMock(choices=[mock_choice])
    mock_openai_instance.chat.completions.create = AsyncMock(return_value=mock_chat_completion)

    with patch("app.services.llm_gateway.AsyncOpenAI", return_value=mock_openai_instance):
        result = await generate_llm_content(
            prompt="Analyze safety",
            tier="fast",
            response_mime_type="application/json",
            client=mock_gemini_client,
        )

        assert result.text == '{"on_topic": true, "injection_attempt": false}'
        call_kwargs = mock_openai_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}
