# Design: Ticket Data Sanitization & Validation

## Architecture & Context
In TecniDesk, ticket intake occurs via `POST /tickets`, which uses `TicketCreate` in `backend/app/schemas/ticket.py`. These tickets represent physical devices brought into the repair workshop and are tracked across all boards, status updates, and public client portals. Cleansing descriptive fields at the schema layer ensures reliable indexing, search consistency, and clean persistence.

## Decisions & Tradeoffs
1. **Pydantic `@field_validator` on `TicketCreate`:**
   - *Decision:* Add validators directly to `TicketCreate` in `app/schemas/ticket.py`.
   - *Why:* Rejects bad inputs immediately with 422 before the router checks client presence or triggers Fernet PIN encryption.

2. **Threshold validation after stripping:**
   - *Decision:* Clean with `.strip()` before checking minimum length (`device_brand` >= 2, `device_model` >= 2, `issue_description` >= 5).
   - *Why:* Prevents deceptive inputs where spaces artificially satisfied the raw character count constraint.

3. **Nullable normalization:**
   - *Decision:* For `client_name`, `client_phone`, `internal_notes`, if `v is not None`, apply `.strip()`. If the result is an empty string `""`, return `None`.
   - *Why:* Keeps optional database columns clean with SQL `NULL` instead of whitespace strings.

## File Changes
- **`backend/app/schemas/ticket.py`**:
  - Add `field_validator` import if not already present.
  - Add `sanitize_brand_and_model`, `sanitize_issue_description`, and `sanitize_optional_fields` validators to `TicketCreate`.
- **`backend/tests/unit/test_ticket_schemas.py`**:
  - Add unit test suite testing whitespace stripping, rejection of blank/short fields, and normalization of optional fields.
