import json
from uuid import UUID
from typing import List
from google import genai
from google.genai import types
from app.config import get_settings
from app.models.diagnostic import DiagnosticCase
from app.schemas.diagnostic import DiagnosticResponse, GroundedCitation
import logging

logger = logging.getLogger(__name__)

class ExplanationService:
    @staticmethod
    def _build_prompt(symptom: str, retrieved_cases: List[DiagnosticCase]) -> str:
        prompt = f"You are a master technician diagnosing a device issue.\n"
        prompt += f"Symptom: {symptom}\n\n"
        prompt += "Context from historical cases (these are your ONLY source of truth):\n"
        for i, case in enumerate(retrieved_cases):
            prompt += f"Case ID: {case.id}\n"
            prompt += f"Brand/Model: {case.device_brand} {case.device_model}\n"
            prompt += f"Symptom: {case.symptom_text}\n"
            prompt += f"Cause: {case.diagnosed_cause}\n"
            prompt += f"Solution: {case.solution_applied}\n"
            prompt += f"Source Type: {case.source_type}\n\n"
        
        prompt += "Using ONLY the context provided above, provide a diagnostic response.\n"
        prompt += "You MUST cite the Case ID exactly as provided.\n"
        prompt += "The diagnosed_cause and solution_applied in your citations MUST perfectly match the text in the context.\n"
        prompt += "If the context does not contain sufficient information to make a diagnosis, set had_sufficient_evidence to false and leave the rest appropriately empty or general.\n"
        return prompt

    @staticmethod
    async def generate_explanation(
        symptom: str, 
        retrieved_cases: List[DiagnosticCase],
        best_distance: float
    ) -> DiagnosticResponse:
        
        if not retrieved_cases or best_distance > 0.40:
            return DiagnosticResponse(
                had_sufficient_evidence=False,
                summary_explanation="No similar historical cases found.",
                probable_cause="Unknown",
                recommended_steps=[],
                citations=[],
                similarity_distance=best_distance,
                maturity_source="none"
            )

        settings = get_settings()
        client = genai.Client(api_key=settings.gemini_api_key)
        
        prompt = ExplanationService._build_prompt(symptom, retrieved_cases)
        
        response = await client.aio.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,

                response_mime_type="application/json",
                response_schema=DiagnosticResponse,
            )
        )
        
        try:
            resp_dict = json.loads(response.text)
            diagnosis = DiagnosticResponse(**resp_dict)
            diagnosis.similarity_distance = best_distance
            
            # Determine maturity source
            if any(c.source_type == 'real_validated' for c in diagnosis.citations):
                diagnosis.maturity_source = 'real_validated'
            elif diagnosis.citations:
                diagnosis.maturity_source = 'synthetic'
            else:
                diagnosis.maturity_source = 'none'

            # Run deterministic verification
            if not ExplanationService.verify_grounded_citations(diagnosis, retrieved_cases):
                return DiagnosticResponse(
                    had_sufficient_evidence=False,
                    summary_explanation="Generated explanation failed factual verification against context.",
                    probable_cause="Unknown",
                    recommended_steps=[],
                    citations=[],
                    similarity_distance=best_distance,
                    maturity_source="none"
                )

            return diagnosis

        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return DiagnosticResponse(
                had_sufficient_evidence=False,
                summary_explanation="Failed to generate a valid explanation.",
                probable_cause="Unknown",
                recommended_steps=[],
                citations=[],
                similarity_distance=best_distance,
                maturity_source="none"
            )

    @staticmethod
    def verify_grounded_citations(
        diagnosis: DiagnosticResponse,
        retrieved_cases: List[DiagnosticCase]
    ) -> bool:
        case_map = {str(case.id): case for case in retrieved_cases}
        for citation in diagnosis.citations:
            cit_id_str = str(citation.case_id)
            if cit_id_str not in case_map:
                return False  # Fabricated case ID
            matched_case = case_map[cit_id_str]
            if citation.diagnosed_cause.strip() != matched_case.diagnosed_cause.strip():
                return False  # Paraphrased or altered cause
            if citation.solution_applied.strip() != matched_case.solution_applied.strip():
                return False  # Paraphrased or altered solution
        return True
