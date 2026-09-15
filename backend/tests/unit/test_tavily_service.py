"""
Unit tests for tavily_service (Web Search Pre-Fetch for Ohm Technical Reasoning).
"""
import pytest
import respx
import httpx
from unittest.mock import patch

from app.services.tavily_service import search_technical_web, TAVILY_SEARCH_URL
from app.config import Settings


@pytest.fixture
def mock_tavily_settings():
    test_settings = Settings(
        tavily_api_key="tvly-test-key-12345",
        tavily_timeout_seconds=2.5,
    )
    with patch("app.services.tavily_service.get_settings", return_value=test_settings):
        yield test_settings


@pytest.mark.asyncio
@respx.mock
async def test_search_technical_web_success(mock_tavily_settings):
    """Test successful search with enriched device context and filtered results."""
    mock_response_data = {
        "query": "iPhone 13 Pro Max no enciende consumo 0.02A",
        "results": [
            {
                "title": "Guía Reparación iPhone 13 Pro Max",
                "url": "https://reparaciones.com/iphone-13-pm",
                "content": "Revisar línea PP_VDD_MAIN y corto en condensador C1204.",
                "score": 0.95,
            },
            {
                "title": "Diagrama esquemático",
                "url": "https://esquematicos.com/diagrama-13",
                "content": "Valores en escala de diodos para PMIC principal.",
                "score": 0.88,
            },
            {
                "title": "",  # Empty title should be skipped
                "url": "https://invalid.com",
                "content": "No title",
            },
        ],
    }

    route = respx.post(TAVILY_SEARCH_URL).respond(
        status_code=200,
        json=mock_response_data,
    )

    results = await search_technical_web(
        query="no enciende consumo 0.02A",
        device_context="iPhone 13 Pro Max",
        max_results=3,
    )

    assert route.called
    sent_json = route.calls.last.request.read().decode("utf-8")
    assert "iPhone 13 Pro Max no enciende consumo 0.02A" in sent_json

    assert len(results) == 2
    assert results[0]["title"] == "Guía Reparación iPhone 13 Pro Max"
    assert results[0]["url"] == "https://reparaciones.com/iphone-13-pm"
    assert "PP_VDD_MAIN" in results[0]["content"]
    assert results[1]["title"] == "Diagrama esquemático"


@pytest.mark.asyncio
async def test_search_technical_web_missing_api_key():
    """Test that missing API key returns empty list immediately without network call."""
    test_settings = Settings(tavily_api_key="", tavily_timeout_seconds=2.5)
    with patch("app.services.tavily_service.get_settings", return_value=test_settings):
        results = await search_technical_web("falla de carga", device_context="Samsung A52")
        assert results == []


@pytest.mark.asyncio
async def test_search_technical_web_empty_query(mock_tavily_settings):
    """Test that empty query returns empty list without network call."""
    results = await search_technical_web("   ")
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_search_technical_web_timeout(mock_tavily_settings):
    """Test that HTTP timeout fails open and returns empty list."""
    respx.post(TAVILY_SEARCH_URL).mock(
        side_effect=httpx.TimeoutException("Connection timed out after 2.5s")
    )

    results = await search_technical_web(
        query="corto en linea vdd",
        device_context="Xiaomi Note 11",
    )
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_search_technical_web_http_error(mock_tavily_settings):
    """Test that 500 error from Tavily fails open and returns empty list."""
    respx.post(TAVILY_SEARCH_URL).respond(
        status_code=500,
        text="Internal Server Error",
    )

    results = await search_technical_web(
        query="linea i2c bloqueada",
        device_context="Motorola G60",
    )
    assert results == []
