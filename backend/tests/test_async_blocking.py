import asyncio
import time
import pytest
import uuid
import resend

from app.services.email_service import send_password_reset_email
from app.services.explanation_service import ExplanationService

class MockCase:
    def __init__(self, id, device_brand, device_model, symptom_text, diagnosed_cause, solution_applied, source_type):
        self.id = id
        self.device_brand = device_brand
        self.device_model = device_model
        self.symptom_text = symptom_text
        self.diagnosed_cause = diagnosed_cause
        self.solution_applied = solution_applied
        self.source_type = source_type

@pytest.fixture
def retrieved_cases():
    return [
        MockCase(
            id=uuid.uuid4(),
            device_brand="Samsung",
            device_model="Galaxy S22",
            symptom_text="Screen flickering",
            diagnosed_cause="Faulty display cable",
            solution_applied="Replaced display cable",
            source_type="real_validated"
        )
    ]

@pytest.mark.asyncio
async def test_async_blocking(monkeypatch, retrieved_cases):
    stop_monitor = False
    max_lag = 0.0

    async def monitor_loop_lag():
        nonlocal max_lag
        while not stop_monitor:
            start = time.perf_counter()
            await asyncio.sleep(0.01) # 10 ms sleep
            elapsed = time.perf_counter() - start
            lag = elapsed - 0.01
            if lag > max_lag:
                max_lag = lag

    monitor_task = asyncio.create_task(monitor_loop_lag())
    
    # Let the monitor start running
    await asyncio.sleep(0.05)

    # --- 1. Test Resend ---
    def mock_resend_send(*args, **kwargs):
        time.sleep(0.5)
        return {"id": "mocked_id"}

    monkeypatch.setattr(resend.Emails, "send", mock_resend_send)
    monkeypatch.setattr("app.services.email_service.settings.resend_api_key", "fake_key")
    monkeypatch.setattr("app.services.email_service.settings.mail_from", "test@test.com")

    await send_password_reset_email("test@example.com", "http://reset")

    # --- 2. Test Gemini ---
    case = retrieved_cases[0]
    class MockResponse:
        text = f'{{"had_sufficient_evidence": true, "summary_explanation": "Based on a similar real case...", "probable_cause": "Faulty display cable", "recommended_steps": ["Replace display cable"], "citations": [{{"case_id": "{case.id}", "source_type": "real_validated", "diagnosed_cause": "Faulty display cable", "solution_applied": "Replaced display cable"}}], "similarity_distance": 0.1, "maturity_source": "real_validated"}}'

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.aio = self.Aio()
        class Aio:
            def __init__(self):
                self.models = self.Models()
            class Models:
                async def generate_content(self, *args, **kwargs):
                    await asyncio.sleep(0.5)
                    return MockResponse()

    monkeypatch.setattr("google.genai.Client", MockClient)

    await ExplanationService.generate_explanation(
        symptom="Screen flickering",
        retrieved_cases=retrieved_cases,
        best_distance=0.1
    )

    stop_monitor = True
    await monitor_task

    # Max allowed lag is 50ms (0.05s)
    assert max_lag < 0.05, f"Event loop was blocked! Max lag: {max_lag*1000:.2f}ms"
