# Tasks: Ohm Administrative Assistant

## 1. Backend Implementation (TDD)
- [x] 1.1 Create schemas `AdminAssistantQueryRequest` and `AdminAssistantQueryResponse` in `backend/app/schemas/admin_assistant.py`
- [x] 1.2 Implement `backend/app/services/admin_assistant_service.py`:
  - Intent classification logic (direct pattern matching + fast LLM fallback)
  - Deterministic metrics queries for `ganancias_del_dia`, `equipos_ingresados_hoy`, and `equipos_sin_tocar`
  - Conversational response synthesis and canned fallback formatter
- [x] 1.3 Create router `backend/app/routers/admin_assistant.py` with `POST /admin/assistant/query` protected by `admin_guard`
- [x] 1.4 Register router in `backend/app/main.py`
- [x] 1.5 Create unit tests in `backend/tests/unit/test_admin_assistant.py`:
  - Classification for each intent token
  - Fallback canned response on unrecognized intent
  - Role protection (technician gets 403)
  - Multi-tenant shop isolation
- [x] 1.6 Verify backend unit tests pass

## 2. Frontend Implementation & Tests
- [x] 2.1 Create `frontend/src/api/adminAssistant.js` with `sendAdminAssistantQuery`
- [x] 2.2 Update `frontend/src/features/technician/AiChatDrawer.jsx` to support `context="admin"`:
  - Admin header branding
  - Quick-action chips (Ganancias de hoy, Equipos ingresados hoy, Equipos sin tocar)
  - Routing messages to `sendAdminAssistantQuery`
  - Hiding ticket diagnostic RAG controls
- [x] 2.3 Mount `AiChatBubble` and `AiChatDrawer` with `context="admin"` in `frontend/src/features/admin/AdminDashboard.jsx`
- [x] 2.4 Create frontend unit tests in `frontend/src/tests/features/admin/AdminAssistant.test.jsx`:
  - Quick chips display in admin mode
  - Clicking chips dispatches to admin query API
  - General free text dispatch in admin mode
- [x] 2.5 Verify frontend unit tests pass with `npx vitest run`

## 3. Verification & Archival
- [x] 3.1 Run full backend and frontend regression suites
- [x] 3.2 Update `PROJECT_STATE.md`, `README.md`, and `GEMINI.md`
- [x] 3.3 Archive change into `openspec/changes/archive/` and promote spec to `openspec/specs/admin-assistant/spec.md`
