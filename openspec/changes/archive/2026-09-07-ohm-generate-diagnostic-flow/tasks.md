# Tasks: Ohm Controlled Diagnostic Generation & Application

## 1. Database Schema & Migration
- [x] 1.1 Update Ticket model in backend/app/models/ticket.py with draft_diagnostic and diagnostic_applied_at
- [x] 1.2 Create Alembic migration script revising c4d5e6f7a8b9
- [x] 1.3 Add Pydantic schemas in backend/app/schemas/ticket.py: DraftDiagnosticResponse, ApplyDiagnosticRequest, and expose fields in detail responses

## 2. Backend Implementation (TDD)
- [x] 2.1 Create backend test suite backend/tests/unit/test_diagnostic_generation.py covering:
  - Status gating (400 when not EN_REPARACION or LISTO_PARA_RETIRAR)
  - Empty history check (400)
  - Duplicate generation block (409)
  - Gemini failure resilience (draft remains None on 503)
  - Apply without draft (400)
  - Apply without edit (applies original draft)
  - Apply with edit (applies and persists edited version)
- [x] 2.2 Implement generate_final_diagnostic and prompt synthesis with Gemini retry loop in service layer
- [x] 2.3 Implement POST /tickets/{ticket_id}/generate-diagnostic and POST /tickets/{ticket_id}/apply-diagnostic in backend/app/routers/tickets.py
- [x] 2.4 Verify all backend tests pass (GREEN)

## 3. Frontend Implementation & Test Refactoring
- [x] 3.1 Remove per-bubble Aplicar al Diagnóstico button in AiChatDrawer.jsx
- [x] 3.2 Add Generar diagnóstico con Ohm, review area, and Aplicar flow in TechnicianWorkModal.jsx
- [x] 3.3 Refactor TechnicianPortal.test.jsx (line 680) to reflect the new decoupled flow
- [x] 3.4 Verify full frontend test suite passes with npx vitest run

## 4. Verification & Archival
- [x] 4.1 Run full regression suites (backend + frontend)
- [x] 4.2 Archive change to openspec/changes/archive/ and record permanent spec
