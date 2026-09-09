# Tasks: Technician Data Sanitization & Validation

## 1. Unit Tests (TDD - RED Phase)
- [x] 1.1 Create `backend/tests/unit/test_technician_schemas.py` with test cases for full_name trimming, blank rejection, and optional field normalization (RED)
- [x] 1.2 Verify tests fail before implementation

## 2. Schema Implementation (TDD - GREEN Phase)
- [x] 2.1 Add `@field_validator("full_name")` and `@field_validator("contact", "declared_specialty")` to `TechnicianCreate` in `backend/app/schemas/technician.py`
- [x] 2.2 Add `@field_validator("full_name")` and `@field_validator("contact", "declared_specialty")` to `TechnicianUpdate` in `backend/app/schemas/technician.py`
- [x] 2.3 Verify `test_technician_schemas.py` passes with `pytest tests/unit/test_technician_schemas.py -v` (GREEN)

## 3. Full Verification & Regression
- [x] 3.1 Run all schema unit tests (`test_auth_schemas`, `test_inventory_schemas`, `test_technician_schemas`)
- [x] 3.2 Verify spec compliance matrix
