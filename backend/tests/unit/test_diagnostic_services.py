"""
Pruebas unitarias para los servicios y modelos de diagnóstico (Fase 1).
"""
import pytest
import respx
import httpx
from uuid import uuid4

from app.config import get_settings
from app.core.exceptions import EmbeddingServiceUnavailableError
from app.services.embedding_service import (
    EmbeddingService,
    QUERY_PREFIX,
    DOCUMENT_PREFIX,
    MAX_CHAR_LENGTH,
)
from app.models.diagnostic import (
    DiagnosticCase,
    DiagnosticConversation,
    DiagnosticMessage,
    DiagnosticQueryLog,
)


@pytest.mark.asyncio
async def test_format_helpers():
    """Verifica que las funciones de formateo para query y document sean consistentes."""
    query_str = EmbeddingService.format_query_text(
        brand="Apple",
        model="iPhone 13",
        symptom="Pantalla en negro tras caída",
    )
    assert query_str == "Brand: Apple | Model: iPhone 13 | Symptom: Pantalla en negro tras caída"

    doc_str = EmbeddingService.format_document_text(
        brand="Samsung",
        model="Galaxy S22",
        symptom="No carga",
        cause="Puerto USB-C sulfatado",
        solution="Reemplazo de módulo sub-placa de carga",
    )
    assert doc_str == "Brand: Samsung | Model: Galaxy S22 | Symptom: No carga | Cause: Puerto USB-C sulfatado | Solution: Reemplazo de módulo sub-placa de carga"


@pytest.mark.asyncio
@respx.mock
async def test_get_embedding_query_success():
    """Verifica la generación exitosa de embedding para consultas con prefijo search_query:."""
    settings = get_settings()
    endpoint = f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"
    mock_vector = [0.123] * 768

    route = respx.post(endpoint).mock(
        return_value=httpx.Response(200, json={"model": "nomic-embed-text-v2-moe:latest", "embeddings": [mock_vector]})
    )

    text = "Brand: Apple | Model: iPhone 13 | Symptom: Pantalla rota"
    embedding = await EmbeddingService.get_embedding(text, is_query=True)

    assert embedding == mock_vector
    assert route.called
    last_req = route.calls.last.request
    import json
    body = json.loads(last_req.content)
    assert body["model"] == "nomic-embed-text-v2-moe:latest"
    assert body["input"].startswith(QUERY_PREFIX)
    assert text in body["input"]


@pytest.mark.asyncio
@respx.mock
async def test_get_embedding_document_and_truncation():
    """Verifica que un texto superior a 1500 caracteres sea truncado de forma segura y use prefijo search_document:."""
    settings = get_settings()
    endpoint = f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"
    mock_vector = [-0.05] * 768

    route = respx.post(endpoint).mock(
        return_value=httpx.Response(200, json={"model": "nomic-embed-text-v2-moe:latest", "embeddings": [mock_vector]})
    )

    long_text = "A" * 3000
    embedding = await EmbeddingService.get_embedding(long_text, is_query=False)

    assert embedding == mock_vector
    assert route.called
    last_req = route.calls.last.request
    import json
    body = json.loads(last_req.content)
    assert body["input"].startswith(DOCUMENT_PREFIX)
    # The truncated text portion must be exactly MAX_CHAR_LENGTH characters
    payload_content = body["input"][len(DOCUMENT_PREFIX):]
    assert len(payload_content) == MAX_CHAR_LENGTH


@pytest.mark.asyncio
@respx.mock
async def test_get_embedding_service_unavailable_connection_error():
    """Verifica que se lance EmbeddingServiceUnavailableError ante fallo de conexión."""
    settings = get_settings()
    endpoint = f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"

    respx.post(endpoint).mock(side_effect=httpx.ConnectError("Connection refused"))

    with pytest.raises(EmbeddingServiceUnavailableError) as exc_info:
        await EmbeddingService.get_embedding("Texto de prueba", is_query=True)

    assert "Local embedding service unreachable" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_get_embedding_service_500_error():
    """Verifica que se lance EmbeddingServiceUnavailableError si Ollama devuelve error HTTP 500."""
    settings = get_settings()
    endpoint = f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"

    respx.post(endpoint).mock(return_value=httpx.Response(500, text="Internal Server Error"))

    with pytest.raises(EmbeddingServiceUnavailableError) as exc_info:
        await EmbeddingService.get_embedding("Texto de prueba", is_query=False)

    assert "Local embedding service unreachable" in str(exc_info.value)


def test_diagnostic_models_instantiation():
    """Verifica la correcta instanciación de los modelos SQLAlchemy de diagnóstico."""
    case_id = uuid4()
    shop_id = uuid4()
    mock_vector = [0.0] * 768

    case = DiagnosticCase(
        id=case_id,
        shop_id=shop_id,
        source_type="synthetic",
        device_brand="Xiaomi",
        device_model="Redmi Note 11",
        symptom_text="Reinicios constantes",
        diagnosed_cause="Fallo en botón power o PMIC",
        solution_applied="Limpieza de flex de encendido",
        repair_time_minutes=45,
        estimated_cost=25.00,
        embedding=mock_vector,
    )
    assert case.id == case_id
    assert case.source_type == "synthetic"
    assert len(case.embedding) == 768

    conv = DiagnosticConversation(
        diagnostic_case_id=case_id,
        ticket_id=uuid4(),
        technician_id=uuid4(),
        shop_id=shop_id,
        status="open",
    )
    assert conv.status == "open"

    msg = DiagnosticMessage(
        conversation_id=conv.id,
        role="technician",
        content="El cliente menciona que ocurrió tras una actualización.",
    )
    assert msg.role == "technician"

    log = DiagnosticQueryLog(
        shop_id=shop_id,
        query_text="Xiaomi Redmi Note 11 reinicios constantes",
        top_case_id=case_id,
        source_type_used="synthetic",
        similarity_score=0.92,
        had_sufficient_evidence=True,
    )
    assert log.had_sufficient_evidence is True
