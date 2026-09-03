# Design: Sanitize WhatsApp Number in Public Endpoints

## Architecture Decisions

Instead of adding complex database regex or altering the schema (which might break shop profile management where formatted display numbers are allowed), we will perform helper-level sanitization when constructing the public response in `_enrich_response`.

A small helper function `_sanitize_phone(phone_str: str | None) -> str | None` will use a regex (`re.sub(r"\D", "", phone_str)`) to strip out all non-digit characters. If the resulting string is empty or `phone_str` is `None`, it returns `None`.

## File Changes

- `backend/app/api/v1/endpoints/tracking.py`:
  - Import `re`.
  - Add helper function `_sanitize_phone(phone_str: str | None) -> str | None`.
  - Update `_enrich_response` to apply `_sanitize_phone` on `contact_whatsapp`.

## Alternatives Considered

- **Sanitizing at DB Insertion/Update (Shop model):** Rejected for now to avoid side effects on shop management views where formatted text might be expected, keeping the scope minimal and safe for this change.
