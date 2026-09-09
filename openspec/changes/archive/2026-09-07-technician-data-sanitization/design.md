# Design: Technician Data Sanitization & Validation

## Architecture & Context
The technician domain models are defined in `backend/app/schemas/technician.py`. Requests to register a technician (`POST /technicians`) or edit their profile (`PATCH /technicians/{id}`) pass through `TechnicianCreate` and `TechnicianUpdate`. Enforcing field sanitization directly within Pydantic models guarantees clean data ingestion before records reach service transactions or database rows.

## Decisions & Tradeoffs
1. **Schema-level `@field_validator` vs. Service-level checks:**
   - *Decision:* Implement `@field_validator` in `TechnicianCreate` and `TechnicianUpdate`.
   - *Why:* Schema validators reject malformed payloads immediately with HTTP 422 before starting database sessions or executing service business logic.
   - *Tradeoff:* Keeps domain sanitization declarative and cohesive with existing Pydantic models.

2. **Normalizing empty strings to `None` for optional fields:**
   - *Decision:* For `contact` and `declared_specialty`, if the stripped string is empty, convert to `None`.
   - *Why:* In SQL, nullable columns should hold `NULL` rather than whitespace or empty string `""` to maintain clean queries (`IS NULL`), indexing, and consistent API responses.

3. **Reusing validator logic:**
   - *Decision:* Define classmethod validators for `full_name` and optional string fields (`contact`, `declared_specialty`).

## File Changes
- **`backend/app/schemas/technician.py`**:
  - Import `field_validator` from `pydantic`.
  - Add `sanitize_full_name` and `sanitize_optional_text` validators to `TechnicianCreate`.
  - Add `sanitize_full_name` and `sanitize_optional_text` validators to `TechnicianUpdate`.
- **`backend/tests/unit/test_technician_schemas.py`**:
  - Unit tests asserting trimming, rejection of short/empty names, and conversion of whitespace to `None` for optional fields.
