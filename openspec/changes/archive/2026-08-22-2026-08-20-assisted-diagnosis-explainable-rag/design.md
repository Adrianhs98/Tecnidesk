# Design: AI-Assisted Diagnostic System with Explainable Reasoning and Local Embeddings

**Status**: draft  
**Date**: 2026-08-20  
**Author**: SDD Architect  

---

## 1. Architecture Overview

```
+-----------------------------------------------------------------------------------+
| FRONTEND (React 19 + Vite)                                                        |
| - DiagnosticModal.jsx: Shows diagnosis, confidence badge, collapsible citations  |
| - NewTicketModal.jsx: onBlur initial suggestion preview                           |
| - DiagnosticChatDrawer: Human-in-the-loop correction chat                         |
+----------------------------------------+------------------------------------------+
                                         | REST (JWT + subscription_guard)
                                         v
+-----------------------------------------------------------------------------------+
| BACKEND (FastAPI + SQLAlchemy 2.0 Async)                                          |
|                                                                                   |
|  1. /tickets/{id}/diagnose                                                        |
|     - Truncates symptom to <512 tokens                                            |
|     - Calls Ollama via Tailscale Funnel with prefix 'search_query: '              |
|     - Queries pgvector (HNSW cosine distance) filtered by shop_id / tenant        |
|     - If distance > 0.40 -> returns INSUFFICIENT_EVIDENCE fallback                |
|     - Else calls Gemini 3.7 Flash (temp 0.0, structured JSON, high thinking)      |
|     - Runs deterministic post-verifier (exact field match on cited case_ids)      |
|     - Logs query to diagnostic_query_log                                          |
|                                                                                   |
|  2. /tickets/{id}/diagnostic-chat & /confirm-correction                           |
|     - Manages conversation turns in diagnostic_conversations / messages           |
|     - On confirmation: embeds new case with 'search_document: ' & inserts as      |
|       source_type='real_validated' with derived_from_case_id pointing to original |
+-----------------------+------------------------------------+----------------------+
                        |                                    |
            HTTP/JSON   |                        SQL (Async) | HTTP (Google GenAI)
            (Tailscale) |                                    |
                        v                                    v
+----------------------------------+   +-------------------------------+   +-----------------------+
| MAC MINI M1 (Local Ollama)       |   | SUPABASE (PostgreSQL 16)      |   | GOOGLE AI STUDIO      |
| - nomic-embed-text-v2-moe:latest |   | - extension: vector           |   | - gemini-3.7-flash    |
| - Port: 11434 -> Tailscale Funnel|   | - diagnostic_cases            |   |   (High thinking)     |
| - Output: 768 dims (512 ctx limit|   | - diagnostic_conversations    |   | - Structured JSON mode|
+----------------------------------+   | - diagnostic_messages         |   | - Zero temperature    |
                                       | - diagnostic_query_log        |   +-----------------------+
                                       +-------------------------------+
```

---

## 2. Database Design & DDL

### 2.1 New Tables

```sql
-- 1. Enable pgvector in extensions schema
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

-- 2. Diagnostic Cases (Synthetic benchmarks + Real workshop outcomes)
CREATE TABLE diagnostic_cases (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id              UUID REFERENCES shops(id) ON DELETE CASCADE, -- NULL for global synthetic cases
    origin_ticket_id     UUID REFERENCES tickets(id) ON DELETE SET NULL, -- populated if real_validated
    derived_from_case_id UUID REFERENCES diagnostic_cases(id) ON DELETE SET NULL, -- points to original synthetic case
    source_type          VARCHAR(20) NOT NULL CHECK (source_type IN ('synthetic', 'real_validated')),
    device_brand         VARCHAR(100) NOT NULL,
    device_model         VARCHAR(100) NOT NULL,
    symptom_text         TEXT NOT NULL,
    diagnosed_cause      TEXT NOT NULL,
    solution_applied     TEXT NOT NULL,
    repair_time_minutes  INTEGER,
    estimated_cost       NUMERIC(10,2),
    embedding            vector(768) NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for HNSW Cosine Distance search
CREATE INDEX ix_diagnostic_cases_embedding_hnsw
    ON diagnostic_cases USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Composite filter index
CREATE INDEX ix_diagnostic_cases_shop_brand_model
    ON diagnostic_cases (shop_id, device_brand, device_model);

-- 3. Diagnostic Conversations (Human-in-the-loop chat threads)
CREATE TABLE diagnostic_conversations (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostic_case_id UUID REFERENCES diagnostic_cases(id) ON DELETE CASCADE,
    ticket_id          UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    technician_id      UUID NOT NULL REFERENCES technicians(id),
    shop_id            UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    status             VARCHAR(20) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'confirmed', 'corrected', 'abandoned')),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at          TIMESTAMPTZ
);

-- 4. Diagnostic Messages (Chat history)
CREATE TABLE diagnostic_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES diagnostic_conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('system', 'technician', 'assistant')),
    content         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Diagnostic Query Log (Telemetry & Maturity Metric)
CREATE TABLE diagnostic_query_log (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id                 UUID NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
    ticket_id               UUID REFERENCES tickets(id) ON DELETE SET NULL,
    query_text              TEXT NOT NULL,
    top_case_id             UUID REFERENCES diagnostic_cases(id) ON DELETE SET NULL,
    source_type_used        VARCHAR(20),
    similarity_score        FLOAT,
    had_sufficient_evidence BOOLEAN NOT NULL DEFAULT true,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 3. Embedding Pipeline & Local Service Integration

### 3.1 Nomic Task Prefixes & Context Window Constraints
- Model: `nomic-embed-text-v2-moe:latest` (768 dimensions, 512 max input tokens).
- **Document Ingestion Rule**: Text must be formatted as:
  `search_document: Brand: {device_brand} | Model: {device_model} | Symptom: {symptom_text} | Cause: {diagnosed_cause} | Solution: {solution_applied}`
  Prior to prefixing, the string is truncated safely to 1,500 characters (~375 tokens) to guarantee it fits strictly within the 512-token limit.
- **Query Symptom Rule**: Incoming technician symptom query is formatted as:
  `search_query: Brand: {device_brand} | Model: {device_model} | Symptom: {symptom_text}`

### 3.2 Service Implementation (`embedding_service.py`)
```python
import httpx
from app.config import settings

class EmbeddingService:
    @staticmethod
    async def get_embedding(text: str, is_query: bool = False) -> list[float]:
        prefix = "search_query: " if is_query else "search_document: "
        # Safe character truncation to preserve <512 token boundary
        truncated_text = text[:1500]
        payload = {
            "model": "nomic-embed-text-v2-moe:latest",
            "input": f"{prefix}{truncated_text}"
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    f"{settings.local_embedding_service_url}/api/embed",
                    json=payload
                )
                res.raise_for_status()
                data = res.json()
                # Ollama /api/embed returns {"embeddings": [[...]]}
                return data["embeddings"][0]
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise EmbeddingServiceUnavailableError(f"Local embedding service unreachable: {exc}")
```

### 3.3 Custom Exceptions & Error Handling
Defined in `app/core/exceptions.py` (or `app/exceptions.py`):
```python
class EmbeddingServiceUnavailableError(Exception):
    """Raised when the local Ollama/Tailscale embedding endpoint is unreachable or times out."""
    pass
```
The FastAPI exception handler intercepts `EmbeddingServiceUnavailableError` and translates it into an `HTTP 503 Service Unavailable` with payload:
```json
{
  "detail": "Local embedding service unavailable. Please check Tailscale Funnel / Mac mini Ollama status.",
  "code": "EMBEDDING_SERVICE_UNAVAILABLE"
}
```

---

## 4. Grounded Reasoning & Explainability Engine

### 4.1 LLM Configuration & Parameters
- **Model**: `gemini-3.7-flash`
- **Thinking Effort**: Configured with `high` thinking effort (`thinking_budget` or SDK equivalent) for thorough reasoning and validation.
- **Temperature**: `0.0` (zero creativity, deterministic grounding).
- **Output Mode**: Strict JSON Schema enforcement via `response_schema=DiagnosticResponse` and `response_mime_type="application/json"`.

### 4.2 Output Schema (`app/schemas/diagnostic.py`)
```python
from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional

class GroundedCitation(BaseModel):
    case_id: UUID = Field(description="The UUID of the cited diagnostic case")
    source_type: str = Field(description="'synthetic' or 'real_validated'")
    diagnosed_cause: str = Field(description="Exact diagnosed cause string from the case")
    solution_applied: str = Field(description="Exact solution applied string from the case")

class DiagnosticResponse(BaseModel):
    had_sufficient_evidence: bool
    summary_explanation: str
    probable_cause: str
    recommended_steps: List[str]
    citations: List[GroundedCitation]
    similarity_distance: float
    maturity_source: str  # 'real_validated' | 'synthetic' | 'none'
```

### 4.3 Deterministic Field Verification Check
```python
def verify_grounded_citations(
    diagnosis: DiagnosticResponse,
    retrieved_cases: list[DiagnosticCase]
) -> bool:
    case_map = {case.id: case for case in retrieved_cases}
    for citation in diagnosis.citations:
        if citation.case_id not in case_map:
            return False  # Fabricated case ID
        matched_case = case_map[citation.case_id]
        if citation.diagnosed_cause.strip() != matched_case.diagnosed_cause.strip():
            return False  # Paraphrased or altered cause
        if citation.solution_applied.strip() != matched_case.solution_applied.strip():
            return False  # Paraphrased or altered solution
    return True
```

---

## 5. API Endpoints

| Method & Route | Auth & Guard | Request Body | Response Model | Description |
|---|---|---|---|---|
| `POST /tickets/{id}/diagnose` | `subscription_guard` | None (uses ticket's issue_description) | `DiagnosticResponse` | Runs retrieval + LLM synthesis + quote verification. Logs query. |
| `POST /tickets/{id}/diagnostic-chat` | `subscription_guard` | `DiagnosticMessageIn` (`message`) | `DiagnosticMessageResponse` | Appends technician message and returns assistant reasoning response. |
| `POST /tickets/{id}/diagnostic-chat/confirm` | `subscription_guard` | `ConfirmCorrectionIn` (`cause`, `solution`, `cost`, `time`) | `DiagnosticCaseResponse` | Creates new `real_validated` case, generates embedding, closes chat. |
| `GET /diagnostic/maturity-metric` | `subscription_guard` | None | `MaturityMetricResponse` | Returns `% real vs synthetic` queries served in the last 30 days. |

---

## 6. Verification & Test Plan

1. **Unit Tests (`backend/tests/unit/test_diagnostic_services.py`)**:
   - Verify task prefixing logic (`search_query:` vs `search_document:`).
   - Test truncation utility with text > 1500 chars.
   - Test deterministic verifier passing on exact match and failing on hallucinated fields.
2. **Integration Tests (`backend/tests/integration/test_diagnostic_flow.py`)**:
   - Mock Ollama endpoint returning 768-dim mock vector.
   - Insert synthetic + real cases and verify ranking hierarchy (`real_validated` wins on equal distance).
   - Test fallback to `had_sufficient_evidence = false` when distance > 0.40.
   - Test full correction chat flow creating a new `real_validated` case with `derived_from_case_id`.
