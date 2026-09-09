# Proposal: Ticket Data Sanitization & Validation

## Problem
In `backend/app/schemas/ticket.py`, `TicketCreate` defines the core repair order descriptive attributes:
- `device_brand: str = Field(..., min_length=2, max_length=100)`
- `device_model: str = Field(..., min_length=2, max_length=100)`
- `issue_description: str = Field(..., min_length=5)`
- `client_name: str | None = None`
- `client_phone: str | None = None`
- `internal_notes: str | None = None`

Because Pydantic evaluates length constraints before stripping whitespace:
1. Inputs composed purely of whitespace (e.g. `device_brand: "   "`, `device_model: "   "`, `issue_description: "     "`) pass schema validation, resulting in blank tickets in database records, kanban boards, and customer tracking portals.
2. Formatted inputs with accidental whitespace (e.g. `"  Samsung  "`, `"  Galaxy S22  "`, `"  Pantalla rota  "`) are stored with extraneous spaces, degrading search, reporting, and grouping.
3. Optional fields like `client_name`, `client_phone`, and `internal_notes` with whitespace-only values are saved as strings with whitespace instead of being normalized to `None`.

## Solution
1. Add `@field_validator("device_brand", "device_model")` to `TicketCreate`:
   - Strips leading and trailing whitespace.
   - Enforces a minimum length of 2 non-whitespace characters.
   - Raises a `ValueError` if fewer than 2 non-whitespace characters remain.
2. Add `@field_validator("issue_description")` to `TicketCreate`:
   - Strips leading and trailing whitespace.
   - Enforces a minimum length of 5 non-whitespace characters.
   - Raises a `ValueError` if fewer than 5 non-whitespace characters remain.
3. Add `@field_validator("client_name", "client_phone", "internal_notes")` to `TicketCreate`:
   - Strips whitespace.
   - Normalizes empty or whitespace-only inputs to `None`.
4. Add unit test suite in `backend/tests/unit/test_ticket_schemas.py` covering:
   - Trimming of `device_brand`, `device_model`, and `issue_description`.
   - Rejection of whitespace-only strings for brand, model, and issue description.
   - Rejection of short non-whitespace strings below minimum thresholds.
   - Normalization of whitespace-only optional fields to `None`.

## Capabilities
### New Capabilities
- `ticket-data-sanitization`: Schema-level whitespace sanitization and non-empty content validation for ticket repair orders.

## Impact
- **New Files:**
  - `backend/tests/unit/test_ticket_schemas.py`
- **Modified Files:**
  - `backend/app/schemas/ticket.py`
- **Dependencies:** None.
- **Breaking Changes:** None. Prevents blank or malformed repair tickets.
