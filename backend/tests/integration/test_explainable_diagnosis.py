import pytest
import uuid
from app.schemas.diagnostic import DiagnosticResponse, GroundedCitation
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
async def test_explanation_generation_success(retrieved_cases, monkeypatch):
    case = retrieved_cases[0]
    
    class MockResponse:
        text = f'{{"had_sufficient_evidence": true, "summary_explanation": "Based on a similar real case...", "probable_cause": "Faulty display cable", "recommended_steps": ["Replace display cable"], "citations": [{{"case_id": "{case.id}", "source_type": "real_validated", "diagnosed_cause": "Faulty display cable", "solution_applied": "Replaced display cable"}}], "similarity_distance": 0.1, "maturity_source": "real_validated"}}'
        
    class MockClient:
        def __init__(self, *args, **kwargs):
            self.models = self.Models()
        class Models:
            def generate_content(self, *args, **kwargs):
                return MockResponse()

    monkeypatch.setattr("google.genai.Client", MockClient)

    diagnosis = await ExplanationService.generate_explanation(
        symptom="Screen flickering",
        retrieved_cases=retrieved_cases,
        best_distance=0.1
    )
    
    assert diagnosis.had_sufficient_evidence is True
    assert diagnosis.maturity_source == "real_validated"
    assert len(diagnosis.citations) == 1
    assert str(diagnosis.citations[0].case_id) == str(case.id)

@pytest.mark.asyncio
async def test_explanation_generation_hallucinated_fields(retrieved_cases, monkeypatch):
    case = retrieved_cases[0]
    
    class MockResponse:
        # Hallucinated cause
        text = f'{{"had_sufficient_evidence": true, "summary_explanation": "Testing hallucination...", "probable_cause": "Bad battery", "recommended_steps": ["Replace battery"], "citations": [{{"case_id": "{case.id}", "source_type": "real_validated", "diagnosed_cause": "Bad battery", "solution_applied": "Replaced display cable"}}], "similarity_distance": 0.1, "maturity_source": "real_validated"}}'
        
    class MockClient:
        def __init__(self, *args, **kwargs):
            self.models = self.Models()
        class Models:
            def generate_content(self, *args, **kwargs):
                return MockResponse()

    monkeypatch.setattr("google.genai.Client", MockClient)

    diagnosis = await ExplanationService.generate_explanation(
        symptom="Screen flickering",
        retrieved_cases=retrieved_cases,
        best_distance=0.1
    )
    
    # Deterministic verifier should catch the hallucinated cause and fallback to insufficient evidence
    assert diagnosis.had_sufficient_evidence is False
    assert diagnosis.maturity_source == "none"
    assert len(diagnosis.citations) == 0

@pytest.mark.asyncio
async def test_explanation_generation_distance_threshold(retrieved_cases):
    # If best_distance > 0.40, it should short-circuit and return insufficient evidence
    diagnosis = await ExplanationService.generate_explanation(
        symptom="Some symptom",
        retrieved_cases=retrieved_cases,
        best_distance=0.45
    )
    
    assert diagnosis.had_sufficient_evidence is False
    assert diagnosis.summary_explanation == "No similar historical cases found."
