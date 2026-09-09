# Tasks: Inventory Item Name Sanitization & Validation

## 1. Unit Tests (TDD - RED Phase)
- [x] 1.1 Create `backend/tests/unit/test_inventory_schemas.py` with test cases for whitespace stripping, blank rejection, and partial updates (RED)
- [x] 1.2 Verify tests fail before implementation

## 2. Schema Implementation (TDD - GREEN Phase)
- [x] 2.1 Add `@field_validator("item_name")` to `InventoryCreate` in `backend/app/schemas/inventory.py`
- [x] 2.2 Add `@field_validator("item_name")` to `InventoryUpdate` in `backend/app/schemas/inventory.py`
- [x] 2.3 Verify `test_inventory_schemas.py` passes with `pytest tests/unit/test_inventory_schemas.py -v` (GREEN)

## 3. Verification & Regressions
- [x] 3.1 Run auth and inventory unit tests to verify zero regressions
- [x] 3.2 Verify spec compliance matrix
