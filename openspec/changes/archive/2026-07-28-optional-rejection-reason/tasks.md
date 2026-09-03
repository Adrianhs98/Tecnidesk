# Tasks: Optional Rejection Reason

- [x] **Task 1: Create request schema**
  - Add `RejectTicketRequest` in `backend/app/schemas/ticket.py`.
- [x] **Task 2: Update ticket_service.py reject method**
  - Modify `reject_ticket_by_token` to accept `rejection_reason` and prepend it to `ticket.internal_notes`.
- [x] **Task 3: Update reject endpoint in tracking.py**
  - Accept request body `payload: RejectTicketRequest` (which defaults to an empty body with `rejection_reason=None`).
  - Pass the reason to the service layer.
- [x] **Task 4: Add unit and integration tests**
  - Add tests in `backend/tests/unit/test_rejection_reason.py` verifying status updates and notes prepending.
