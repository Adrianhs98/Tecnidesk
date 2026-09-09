# Tasks: Ohm Scope Restriction & Anti Prompt-Injection

## Phase 1: Database & Model
- [x] 1.1 Create `AiSecurityEvent` model in `backend/app/models/ai_security_event.py`
- [x] 1.2 Export `AiSecurityEvent` in `backend/app/models/__init__.py`
- [x] 1.3 Create Alembic migration `backend/alembic/versions/d1e2f3a4b5c6_add_ai_security_events.py` (down_revision `f6a7b8c9d0e1`)
- [x] 1.4 Test migration syntax and alembic upgrade head
 
## Phase 2: Safety Service Module
- [x] 2.1 Implement `backend/app/services/ai_safety_service.py` with `MessageSafetyResult`, `build_safety_classification_prompt`, `classify_message_safety`, `log_ai_security_event`, and `CANNED_REDIRECT_RESPONSE`
- [x] 2.2 Add unit tests in `backend/tests/unit/test_ai_safety_service.py` covering on-topic, off-topic, and injection detection with mocks

## Phase 3: Integration into Ohm Endpoints
- [x] 3.1 Integrate safety classification and logging into `backend/app/routers/diagnostic.py` (`workshop_diagnostic_chat`)
- [x] 3.2 Add anti-injection prompt hardening and sandwich technique in `diagnostic.py`
- [x] 3.3 Integrate safety classification and logging into `backend/app/services/correction_service.py` (`handle_chat_message`)
- [x] 3.4 Add anti-injection prompt hardening in `correction_service.py`
- [x] 3.5 Update unit tests in `test_diagnostic_chat_router.py` and `test_diagnostic_correction.py` to assert safety gating

## Phase 4: Verification & Archival
- [x] 4.1 Run full backend test suite (`pytest`)
- [x] 4.2 Run full frontend test suite (`npm test -- --run`)
- [x] 4.3 Promote spec to `openspec/specs/ohm-scope-and-anti-injection/spec.md`
- [x] 4.4 Archive change into `openspec/changes/archive/2026-09-08-ohm-scope-and-anti-injection/`
- [x] 4.5 Update documentation (`PROJECT_STATE.md`, `GEMINI.md`, `README.md`)
