# SDD Archive: 2026-08-27 Ohm Router, Prompt Localization & Test Suite Stabilization

## 1. Summary of Changes
- **Model Router Identifier Fix:** Corrected `gemini_fast_model` in `backend/app/config.py` from `"gemini-3.5-flash"` to the official, supported Google model ID `"gemini-3.5-flash-lite"`.
- **Diagnostic Assistant Prompt Localization:** Localized and specialized the diagnostic system prompt in `backend/app/routers/diagnostic.py` (`workshop_diagnostic_chat`) to Spanish, tailoring it to microelectronics and hardware repair for smartphone workshops.
- **Dependency & SDK Pinning:**
  - Added `respx==0.23.1` to `backend/requirements.txt` to enable mocked async HTTP tests in the backend suite.
  - Pinned `google-genai==1.2.0` in `backend/requirements.txt` to prevent breaking changes from upstream SDK releases and guarantee reproducible virtual environments.
- **Fixture & Mock Stabilization:**
  - Fixed `tests/unit/test_dashboard_ticket_filters.py` by providing `created_at=now` in the `Shop` model fixture to satisfy non-null database constraints.
  - Updated router unit test in `tests/unit/test_model_router.py` to assert against `"gemini-3.5-flash-lite"`.
  - Refactored `FakeServerError503` in `tests/integration/test_gemini_503_retry.py` to pass a valid `requests.Response` mock with explicit UTF-8 payload to `errors.APIError`, resolving `AttributeError: 'dict' object has no attribute 'body_segments'`.

## 2. Verification
- **Backend (Pytest):** 152 passed (100% success rate across 31 test modules).
- **Frontend (Vitest):** 99 passed (100% success rate across 12 test files).
