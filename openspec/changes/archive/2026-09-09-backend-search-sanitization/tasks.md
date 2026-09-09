# Tasks: Backend Search Query Sanitization

## 1. Unit Tests (TDD - RED Phase)
- [x] 1.1 Create `backend/tests/unit/test_search_sanitization.py` with test cases for ticket, inventory, and client search sanitization (whitespace-only returning all records, padded query trimming)
- [x] 1.2 Run `pytest tests/unit/test_search_sanitization.py` and confirm failure on whitespace-only queries (RED)

## 2. Implementation (TDD - GREEN Phase)
- [x] 2.1 Sanitize `search` in `ticket_service.list_tickets` in `backend/app/services/ticket_service.py`
- [x] 2.2 Sanitize `search` and `sku` in `list_inventory` in `backend/app/routers/inventory.py`
- [x] 2.3 Sanitize `search` in `ClientService.get_clients` in `backend/app/services/client_service.py` and `get_clients` in `backend/app/routers/clients.py`
- [x] 2.4 Run `pytest tests/unit/test_search_sanitization.py` and confirm all tests pass (GREEN)

## 3. Verification & Compliance
- [x] 3.1 Run unit test suite and verify no regressions
- [x] 3.2 Verify all scenarios in `specs/backend-search-sanitization/spec.md`
