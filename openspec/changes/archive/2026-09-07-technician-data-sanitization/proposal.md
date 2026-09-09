# Proposal: Technician Data Sanitization & Validation

## Problem
In `backend/app/schemas/technician.py`, `TechnicianCreate` and `TechnicianUpdate` accept `full_name` as `str = Field(..., min_length=2, max_length=200)` and optional fields `contact` and `declared_specialty` with `max_length`.
Because validation occurs on the raw input strings without whitespace normalization:
1. An administrator can register a technician with `full_name: "   "` (whitespace only), which passes validation because length is 3, creating an unidentifiable technician record.
2. An input like `"  Carlos Mendez  "` is stored with leading and trailing spaces, affecting sorting, UI badges, and assignment displays.
3. Optional fields `contact` and `declared_specialty` with whitespace-only inputs (e.g. `"   "`) are stored as non-null strings of empty spaces instead of being normalized to `None`.

## Solution
1. Add `@field_validator("full_name")` to `TechnicianCreate`:
   - Strips leading and trailing whitespace.
   - Rejects inputs with fewer than 2 non-whitespace characters with a `ValueError`.
2. Add `@field_validator("full_name")` to `TechnicianUpdate`:
   - If `full_name` is not `None`, strips whitespace and rejects inputs with fewer than 2 non-whitespace characters.
3. Add `@field_validator("contact", "declared_specialty")` to both `TechnicianCreate` and `TechnicianUpdate`:
   - Strips whitespace.
   - Normalizes empty or whitespace-only values to `None`.
4. Add unit test suite in `backend/tests/unit/test_technician_schemas.py` covering:
   - Full name trimming and rejection of whitespace-only / short names.
   - Normalization of whitespace-only `contact` and `declared_specialty` to `None`.
   - Retention of clean optional values.
   - Support for partial updates in `TechnicianUpdate`.

## Capabilities
### New Capabilities
- `technician-data-sanitization`: Schema-level whitespace sanitization and non-empty validation for technician records.

## Impact
- **New Files:**
  - `backend/tests/unit/test_technician_schemas.py`
- **Modified Files:**
  - `backend/app/schemas/technician.py`
- **Dependencies:** None.
- **Breaking Changes:** None. Prevents dirty or blank technician records.
