# Design: Optional Rejection Reason

## Architecture Decisions

To allow clients to optionally send a rejection reason, we will add a new Pydantic schema in the schema layer, or define a simple payload parameter in the POST route body.
FastAPI allows optional request bodies using Pydantic. We will define:
```python
from pydantic import BaseModel, Field

class RejectTicketRequest(BaseModel):
    rejection_reason: str | None = Field(default=None, max_length=500)
```

In the service layer, we will update `reject_ticket_by_token` to accept an optional `rejection_reason` string parameter:
```python
async def reject_ticket_by_token(
    db: AsyncSession,
    token: str,
    rejection_reason: str | None = None
) -> Ticket | None:
```

If `rejection_reason` is passed, we prepend it to the ticket's `internal_notes`:
```python
if rejection_reason:
    note_prefix = f"[MOTIVO DE RECHAZO]: {rejection_reason}\n"
    ticket.internal_notes = note_prefix + (ticket.internal_notes or "")
```

## File Changes

- `backend/app/schemas/ticket.py`:
  - Add `RejectTicketRequest` Pydantic class.
- `backend/app/api/v1/endpoints/tracking.py`:
  - Import `RejectTicketRequest`.
  - Update `reject_ticket` endpoint signature to accept `payload: RejectTicketRequest = None` or similar. Since it's optional, we can do `payload: RejectTicketRequest = RejectTicketRequest()`.
  - Pass `payload.rejection_reason` to `ticket_service.reject_ticket_by_token`.
- `backend/app/services/ticket_service.py`:
  - Update `reject_ticket_by_token` to accept `rejection_reason: str | None = None`.
  - Implement prepend logic on `ticket.internal_notes`.

## Alternatives Considered

- **Using a query parameter for reason:** Rejected because it makes it harder to support long/multiline notes. Request body is more standard for optional POST payloads.
