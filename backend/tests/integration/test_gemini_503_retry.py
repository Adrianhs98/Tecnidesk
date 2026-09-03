"""
Pruebas de reintento automático y resiliencia ante errores 503 (Service Unavailable)
de Google Gemini en CorrectionService y ExplanationService.
"""
import uuid
import json
import requests
from datetime import datetime, timezone
import pytest
from google.genai import errors
from app.models.diagnostic import DiagnosticCase
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.technician import Technician
from app.models.ticket import Ticket, TicketStatusEnum
from app.schemas.diagnostic import DiagnosticMessageIn
from app.services.correction_service import CorrectionService
from app.services.explanation_service import ExplanationService


async def _seed_shop_and_ticket(db_session) -> tuple:
    shop = Shop(
        business_name="Test Taller Retry",
        owner_name="Test Owner",
        subdomain=f"taller-retry-{uuid.uuid4().hex[:8]}",
        contact_email=f"retry-{uuid.uuid4().hex[:6]}@test.com",
        contact_whatsapp="593999000002",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    customer = Customer(
        shop_id=shop.id,
        full_name="Cliente Retry",
        phone_number="593987654321",
        email="cliente@retry.com",
    )
    db_session.add(customer)
    await db_session.flush()

    technician = Technician(
        shop_id=shop.id,
        full_name="Técnico Retry",
    )
    db_session.add(technician)
    await db_session.flush()

    ticket = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        issue_description="No carga después de caída",
        status=TicketStatusEnum.EN_REVISION,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    return shop, ticket, technician.id


class FakeServerError503(errors.APIError):
    def __init__(self):
        resp = requests.Response()
        resp.status_code = 503
        resp._content = json.dumps({"error": {"code": 503, "message": "High demand"}}).encode("utf-8")
        resp.encoding = "utf-8"
        super().__init__(503, resp)
        self.code = 503


@pytest.mark.asyncio
async def test_correction_service_503_retry_success(db_session, monkeypatch):
    """Verifica que CorrectionService reintente ante error 503 y tenga éxito si se recupera."""
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)
    call_count = 0

    class MockResponse:
        text = "Diagnóstico ajustado exitosamente tras reintento."

    class MockModels:
        async def generate_content(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise FakeServerError503()
            return MockResponse()

    class MockAio:
        def __init__(self):
            self.models = MockModels()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.aio = MockAio()

    monkeypatch.setattr("app.services.correction_service.genai.Client", MockClient)
    async def fake_sleep(s):
        pass

    monkeypatch.setattr("app.services.correction_service.asyncio.sleep", fake_sleep)

    message_in = DiagnosticMessageIn(message="Revisar corto en línea principal.")
    response = await CorrectionService.handle_chat_message(
        db=db_session,
        shop_id=shop.id,
        technician_id=tech_id,
        ticket_id=ticket.id,
        message_in=message_in,
    )

    assert call_count == 3
    assert response.role == "assistant"
    assert response.content == "Diagnóstico ajustado exitosamente tras reintento."


@pytest.mark.asyncio
async def test_correction_service_503_exhausted_fallback(db_session, monkeypatch):
    """Verifica que CorrectionService devuelva mensaje de fallback si se agotan los reintentos 503."""
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)
    call_count = 0

    class MockModels:
        async def generate_content(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise FakeServerError503()

    class MockAio:
        def __init__(self):
            self.models = MockModels()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.aio = MockAio()

    monkeypatch.setattr("app.services.correction_service.genai.Client", MockClient)
    async def fake_sleep(s):
        pass

    monkeypatch.setattr("app.services.correction_service.asyncio.sleep", fake_sleep)

    message_in = DiagnosticMessageIn(message="Revisar corto.")
    response = await CorrectionService.handle_chat_message(
        db=db_session,
        shop_id=shop.id,
        technician_id=tech_id,
        ticket_id=ticket.id,
        message_in=message_in,
    )

    assert call_count == 3
    assert "alta demanda (503)" in response.content


@pytest.mark.asyncio
async def test_explanation_service_503_retry_success(monkeypatch):
    """Verifica que ExplanationService reintente ante error 503 y genere explicación válida."""
    call_count = 0
    case_id = uuid.uuid4()
    case = DiagnosticCase(
        id=case_id,
        shop_id=uuid.uuid4(),
        device_brand="Apple",
        device_model="iPhone 13",
        symptom_text="No carga",
        diagnosed_cause="Flex de carga sulfatado",
        solution_applied="Cambio de flex de carga",
        source_type="real_validated",
    )

    class MockResponse:
        text = f'''{{
            "had_sufficient_evidence": true,
            "summary_explanation": "Falla común en el flex de carga.",
            "probable_cause": "Flex de carga sulfatado",
            "recommended_steps": ["Medir VBUS", "Reemplazar flex"],
            "similarity_distance": 0.15,
            "maturity_source": "real_validated",
            "citations": [
                {{
                    "case_id": "{case_id}",
                    "diagnosed_cause": "Flex de carga sulfatado",
                    "solution_applied": "Cambio de flex de carga",
                    "source_type": "real_validated"
                }}
            ]
        }}'''

    class MockModels:
        async def generate_content(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise FakeServerError503()
            return MockResponse()

    class MockAio:
        def __init__(self):
            self.models = MockModels()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.aio = MockAio()

    monkeypatch.setattr("app.services.explanation_service.genai.Client", MockClient)
    async def fake_sleep(s):
        pass

    monkeypatch.setattr("app.services.explanation_service.asyncio.sleep", fake_sleep)

    diagnosis = await ExplanationService.generate_explanation(
        symptom="No carga",
        retrieved_cases=[case],
        best_distance=0.15,
    )

    assert call_count == 2
    assert diagnosis.had_sufficient_evidence is True
    assert diagnosis.probable_cause == "Flex de carga sulfatado"


@pytest.mark.asyncio
async def test_explanation_service_503_exhausted_fallback(monkeypatch):
    """Verifica que ExplanationService devuelva respuesta degradada al agotar reintentos 503."""
    call_count = 0
    case_id = uuid.uuid4()
    case = DiagnosticCase(
        id=case_id,
        shop_id=uuid.uuid4(),
        device_brand="Apple",
        device_model="iPhone 13",
        symptom_text="No carga",
        diagnosed_cause="Flex sulfatado",
        solution_applied="Cambio de flex",
        source_type="synthetic",
    )

    class MockModels:
        async def generate_content(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise FakeServerError503()

    class MockAio:
        def __init__(self):
            self.models = MockModels()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.aio = MockAio()

    monkeypatch.setattr("app.services.explanation_service.genai.Client", MockClient)
    async def fake_sleep(s):
        pass

    monkeypatch.setattr("app.services.explanation_service.asyncio.sleep", fake_sleep)

    diagnosis = await ExplanationService.generate_explanation(
        symptom="No carga",
        retrieved_cases=[case],
        best_distance=0.20,
    )

    assert call_count == 3
    assert diagnosis.had_sufficient_evidence is False
    assert "alta demanda (503)" in diagnosis.summary_explanation
