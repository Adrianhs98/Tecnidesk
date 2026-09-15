# Tasks: Client Search Query Sanitization & Service Layer Consolidation

## 1. Tests (TDD - Red)
- [x] 1.1 Add unit tests in `backend/tests/unit/test_search_sanitization.py` for `ClientService` wildcard escaping (`%` and `_`).
- [x] 1.2 Add integration/unit test for `GET /clients` verifying `search` with `max_length=100` returns 422 when exceeded.

## 2. Implementation (TDD - Green)
- [x] 2.1 Update `ClientService.get_clients` in `backend/app/services/client_service.py` with whitespace sanitization and `\\`, `%`, `_` wildcard escaping.
- [x] 2.2 Update `backend/app/routers/clients.py` with `Query(None, max_length=100)` and delegate query execution to `ClientService(db).get_clients`.

## 3. Verification & Refactor
- [x] 3.1 Run pytest on the full backend test suite to ensure zero regressions.
- [x] 3.2 Verify all spec scenarios in `client-listing/spec.md`.
