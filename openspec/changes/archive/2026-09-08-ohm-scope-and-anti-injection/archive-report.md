# Archive Report: Ohm Scope Restriction & Anti Prompt-Injection

## Change Summary
- **Change Name**: ohm-scope-and-anti-injection
- **Completed Date**: 2026-09-08
- **Goal**: Harden Ohm (AI Workshop Assistant) against off-topic queries, quota drain, and prompt-injection attacks through lightweight pre-classification, sandwich prompt defense, canned neutral redirection, and security audit logging.

## Checklist Validation
- [x] Proposal created and approved.
- [x] Specs defined in Given/When/Then scenario format.
- [x] Design documented architecture and decisions.
- [x] Tasks implemented and all checkboxes checked.
- [x] Verification successful (174 backend unit tests + integration tests + 149 frontend tests passing).
- [x] Specs synced to main specs (openspec/specs/ohm-scope-and-anti-injection/spec.md).

## Files Affected
- ackend/app/models/ai_security_event.py (New)
- ackend/app/models/__init__.py (Modified)
- ackend/alembic/versions/d1e2f3a4b5c6_add_ai_security_events.py (New)
- ackend/app/services/ai_safety_service.py (New)
- ackend/app/routers/diagnostic.py (Modified)
- ackend/app/services/correction_service.py (Modified)
- ackend/tests/unit/test_ai_safety_service.py (New)
- ackend/tests/integration/test_diagnostic_chat_router.py (Modified)
- ackend/tests/integration/test_diagnostic_correction.py (Modified)
