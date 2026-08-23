from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import datetime

class GroundedCitation(BaseModel):
    case_id: UUID = Field(description="The UUID of the cited diagnostic case")
    source_type: str = Field(description="'synthetic' or 'real_validated'")
    diagnosed_cause: str = Field(description="Exact diagnosed cause string from the case")
    solution_applied: str = Field(description="Exact solution applied string from the case")

class DiagnosticResponse(BaseModel):
    had_sufficient_evidence: bool = Field(description="Whether the retrieved cases provided sufficient evidence")
    summary_explanation: str = Field(description="Natural language explanation of the diagnosis")
    probable_cause: str = Field(description="The most probable cause of the symptom")
    recommended_steps: List[str] = Field(description="Step-by-step recommendations for repair")
    citations: List[GroundedCitation] = Field(description="List of cited cases used for this diagnosis")
    similarity_distance: float = Field(description="The best similarity distance of the retrieved cases")
    maturity_source: str = Field(description="'real_validated' | 'synthetic' | 'none'")

class DiagnosticQueryLogCreate(BaseModel):
    shop_id: UUID
    ticket_id: Optional[UUID] = None
    query_text: str
    top_case_id: Optional[UUID] = None
    source_type_used: Optional[str] = None
    similarity_score: Optional[float] = None
    had_sufficient_evidence: bool = True

class DiagnosticMessageIn(BaseModel):
    message: str

class DiagnosticMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime

class ConfirmCorrectionIn(BaseModel):
    diagnosed_cause: str
    solution_applied: str
    estimated_cost: Optional[float] = None
    repair_time_minutes: Optional[int] = None

class DiagnosticCaseResponse(BaseModel):
    id: UUID
    source_type: str
    device_brand: str
    device_model: str
    symptom_text: str
    diagnosed_cause: str
    solution_applied: str

class MaturityMetricResponse(BaseModel):
    total_queries: int
    real_validated_percentage: float
    synthetic_percentage: float
