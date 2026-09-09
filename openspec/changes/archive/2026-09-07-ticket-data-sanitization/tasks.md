# Tasks: Ticket Data Sanitization & Validation

## 1. Unit Tests (TDD - RED Phase)
- [x] 1.1 Create `backend/tests/unit/test_ticket_schemas.py` with test cases for brand/model trimming, blank rejection, description thresholds, and optional field normalization (RED)
- [x] 1.2 Verify tests fail before implementation

## 2. Schema Implementation (TDD - GREEN Phase)
- [x] 2.1 Add `@field_validator` for brand and model to `TicketCreate` in `backend/app/schemas/ticket.py`
- [x] 2.2 Add `@field_validator` for issue_description to `TicketCreate` in `backend/app/schemas/ticket.py`
- [x] 2.3 Add `@field_validator` for optional intake fields to `TicketCreate` in `backend/app/schemas/ticket.py`
- [x] 2.4 Verify `test_ticket_schemas.py` passes with `pytest tests/unit/test_ticket_schemas.py -v` (GREEN)

## 3. Full Verification & Regression
- [x] 3.1 Run all schema unit tests (`test_auth_schemas`, `test_inventory_schemas`, `test_technician_schemas`, `test_ticket_schemas`)
- [x] 3.2 Verify spec compliance matrix
