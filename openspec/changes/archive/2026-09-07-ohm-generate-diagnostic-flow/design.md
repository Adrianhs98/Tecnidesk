# Design: Ohm Controlled Diagnostic Generation & Application Flow

## 1. Architectural Overview
This design replaces the arbitrary per-bubble diagnostic injection with a controlled, auditable two-step synthesis pipeline.

`mermaid
sequenceDiagram
    autonumber
    actor Tech as Technician
    participant UI as TechnicianWorkModal / AiChatDrawer
    participant API as FastAPI (tickets.py)
    participant DB as PostgreSQL (Ticket)
    participant Gemini as Google GenAI (gemini-3.6-flash)

    Note over Tech,UI: 1. Technician chats with Ohm during repair
    Tech->>UI: Clicks Generar Diagnóstico
    UI->>API: POST /tickets/{id}/generate-diagnostic
    API->>DB: Check status in (EN_REPARACION, LISTO_PARA_RETIRAR)
    API->>DB: Check draft_diagnostic IS NULL (reject 409 if exists)
    API->>DB: Fetch chat history (reject 400 if empty)
    API->>Gemini: generate_content(synthesis_prompt) with backoff
    Gemini-->>API: Synthesized customer-facing diagnostic
    API->>DB: UPDATE tickets SET draft_diagnostic = :text
    API-->>UI: 200 OK { draft_diagnostic }

    Note over Tech,UI: 2. Technician reviews and optionally edits
    Tech->>UI: Edits text in review area & clicks Aplicar Diagnóstico
    UI->>API: POST /tickets/{id}/apply-diagnostic { edited_diagnostic }
    API->>DB: Check draft_diagnostic IS NOT NULL (reject 400 if null)
    API->>DB: UPDATE tickets SET diagnostic_notes = :final, draft_diagnostic = :final, diagnostic_applied_at = NOW()
    API-->>UI: 200 OK
`

## 2. Database & Alembic Migration
### Table: 	ickets
Two new columns added:
`python
draft_diagnostic: Mapped[str | None] = mapped_column(Text, nullable=True)
diagnostic_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
`

### Alembic Migration
- **Revision ID**: Auto-generated or sequential (e.g., e5f6a7b8c9d0)
- **Down Revision**: c4d5e6f7a8b9 (current head)

## 3. Synthesis Prompt Design
The synthesis prompt takes:
1. Device info: device_brand, device_model, issue_description.
2. Conversation transcript: sorted ascending by creation time.

Prompt instructions:
- Target audience: Customer / Device Owner. Tone: Professional, clear, concise, reassuring, devoid of internal jargon or schematic codes.
- Content constraint: Summarize ONLY what was confirmed and concluded during the repair. Ignore discarded hypotheses.
- Anti-hallucination: Do not introduce hardware faults or repaired parts not discussed in the transcript.

## 4. API Endpoints Contract
### POST /tickets/{ticket_id}/generate-diagnostic
- **Guards**: erify_ticket_technician_access
- **Status Gating**: 	icket.status in (EN_REPARACION, LISTO_PARA_RETIRAR) (else 400)
- **Idempotency / Single Generation**: 	icket.draft_diagnostic is None (else 409)
- **Conversation Check**: len(messages) > 0 (else 400)
- **Retry Policy**: 3 attempts (1s, 2s, 4s) on 503 / APIError.
- **Response**: DraftDiagnosticResponse(draft_diagnostic=text)

### POST /tickets/{ticket_id}/apply-diagnostic
- **Guards**: erify_ticket_technician_access
- **Prerequisite**: 	icket.draft_diagnostic is not None (else 400)
- **Request Body**:
  `python
  class ApplyDiagnosticRequest(BaseModel):
      edited_diagnostic: str | None = None
  `
- **Action**:
  - inal_text = (payload.edited_diagnostic.strip() if payload.edited_diagnostic else None) or ticket.draft_diagnostic
  - 	icket.draft_diagnostic = final_text
  - 	icket.diagnostic_notes = final_text
  - 	icket.diagnostic_applied_at = datetime.now(timezone.utc)
- **Response**: Updated TicketListResponse or status message.

## 5. Frontend Decoupling
1. In AiChatDrawer.jsx:
   - Remove <button data-testid=apply-to-diagnosis-btn>.
   - Keep <button data-testid=confirm-rag-btn> (Confirmar Aprendizaje (RAG)).
2. In TechnicianWorkModal.jsx:
   - Under Diagnóstico y Notas Técnicas, display:
     - Generar con Ohm button (active if status is eligible, disabled with tooltip if already generated or ineligible).
     - Editable review textarea showing draft_diagnostic.
     - Aplicar al Ticket button (enabled when draft_diagnostic is present).
