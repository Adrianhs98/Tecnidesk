# Proposal: Ohm Controlled Diagnostic Generation & Application Flow

## Problem
In the current technician workbench workflow, the Aplicar al Diagnóstico action button is rendered inside every individual assistant message bubble in the active ticket chat (AiChatDrawer.jsx). This design causes several major operational issues:
1. **Premature & Exploratory Pollution**: Early exploratory thoughts, partial testing suggestions (e.g. check the charging IC), or discarded hypotheses can be pushed directly to 	icket.diagnostic_notes, which is immediately rendered in the customer public tracking portal.
2. **Lack of Customer-Oriented Synthesis**: The raw dialogue between the technician and Ohm is internal technical jargon, not a coherent, customer-facing final diagnosis.
3. **Unrestricted Free-Text Overwrite**: The current frontend triggers PATCH /tickets/{id} appending arbitrary text without a gatekeeper ensuring that an AI-synthesized conclusion actually occurred.

## Solution
Implement a formal two-step diagnostic publication pipeline with strict backend gating:
1. **Controlled Synthesis Step (POST /tickets/{id}/generate-diagnostic)**:
   - Gated to tickets in EN_REPARACION or LISTO_PARA_RETIRAR status.
   - Enforces the one-time per ticket invariant: returns 409 Conflict if draft_diagnostic is already populated.
   - Verifies existing non-empty conversation history with Ohm (400 Bad Request if empty).
   - Generates a customer-facing synthesized diagnostic using Gemini 3.6 Flash with exponential backoff retry.
   - Persists the result into a new database column Ticket.draft_diagnostic (private, not exposed to the public tracking portal).
2. **Controlled Publication Step (POST /tickets/{id}/apply-diagnostic)**:
   - Enforces that draft_diagnostic has already been generated (400 Bad Request if None).
   - Accepts an optional payload { edited_diagnostic?: string } allowing the technician to make manual adjustments or corrections before publishing.
   - Updates Ticket.diagnostic_notes (the customer-facing field) and timestamps Ticket.diagnostic_applied_at.
   - Records the edited version into Ticket.draft_diagnostic for audit fidelity.
3. **UI / UX Refinement**:
   - Remove the per-bubble Aplicar al Diagnóstico button from AiChatDrawer.jsx.
   - Add a dedicated Generar diagnóstico con Ohm action in TechnicianWorkModal.jsx and AiChatDrawer.jsx.
   - Provide an editable review area pre-filled with draft_diagnostic.
   - Add an Aplicar Diagnóstico button that calls the new publication endpoint.

## Capabilities
### New Capabilities
- ohm-diagnostic-generation: Two-step AI-assisted diagnostic synthesis and publication flow with state gating, single-generation enforcement, and manual review.

## Impact
- **Backend Schema & Migrations:**
  - Add draft_diagnostic: Text (nullable) and diagnostic_applied_at: DateTime(timezone=True) (nullable) to Ticket model.
  - New Alembic migration revising c4d5e6f7a8b9.
- **Backend Endpoints:**
  - POST /tickets/{ticket_id}/generate-diagnostic
  - POST /tickets/{ticket_id}/apply-diagnostic
- **Frontend Components:**
  - AiChatDrawer.jsx: Remove per-bubble apply button; integrate generation trigger / status.
  - TechnicianWorkModal.jsx: Add review textarea and apply action button.
- **Testing:**
  - Unit & integration tests in ackend/tests/ covering status gating, empty history, 409 duplicate generation, 503 retry resilience, and apply with/without manual edits.
  - Vitest update in TechnicianPortal.test.jsx adapting legacy per-bubble test to the new two-step flow.
