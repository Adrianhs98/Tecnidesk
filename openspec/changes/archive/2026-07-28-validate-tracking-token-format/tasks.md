# Tasks: Validate Tracking Token Format

- [x] **Task 1: Update endpoint signature in tracking.py**
  - Import `UUID` from standard `uuid` module.
  - Change `tracking_token` path parameter type from `str` to `UUID` in `get_public_ticket`, `approve_ticket`, and `reject_ticket`.
- [x] **Task 2: Convert UUID to string for ticket_service calls**
  - Pass `str(tracking_token)` to `ticket_service.get_ticket_by_tracking_token`, `approve_ticket_by_token`, and `reject_ticket_by_token`.
- [x] **Task 3: Add integration/unit test for invalid tracking_token format**
  - Add test in `backend/tests/` to verify that invalid tokens return HTTP 422 immediately.
