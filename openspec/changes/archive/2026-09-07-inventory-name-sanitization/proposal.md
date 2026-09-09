# Proposal: Inventory Item Name Sanitization & Validation

## Problem
In `backend/app/schemas/inventory.py`, `InventoryCreate` and `InventoryUpdate` define `item_name` with `min_length=2, max_length=300`. However, Pydantic's length check counts raw string characters before stripping whitespace. As a result:
1. An input consisting purely of spaces (e.g. `"   "`) passes validation because its raw length is 3, allowing blank items to be inserted into the database.
2. An item name with leading or trailing whitespace (e.g. `"  Display Samsung A12  "`) is stored with redundant spaces, causing duplicate or messy records in searches and filters.
3. An input like `"a "` has raw length 2, but only 1 non-whitespace character.

## Solution
1. Add a Pydantic `@field_validator("item_name")` to `InventoryCreate`:
   - Strips leading and trailing whitespace with `.strip()`.
   - Enforces that the stripped name has a minimum length of 2 characters.
   - Raises a `ValueError` if the stripped name has fewer than 2 non-whitespace characters.
2. Add an equivalent `@field_validator("item_name")` to `InventoryUpdate`:
   - If `item_name` is provided (not `None`), strips leading and trailing whitespace.
   - Enforces a minimum length of 2 characters after stripping.
   - Raises a `ValueError` if fewer than 2 non-whitespace characters remain.
3. Add unit test suite in `backend/tests/unit/test_inventory_schemas.py` covering:
   - Valid trimmed item names are preserved.
   - Names with leading/trailing whitespace are stripped and saved cleanly.
   - Whitespace-only strings are rejected with validation error.
   - Strings with fewer than 2 non-whitespace characters (e.g. `"a "`) are rejected.
   - `InventoryUpdate` with `None` is accepted (partial update), but invalid strings are rejected.

## Capabilities
### Modified Capabilities
- `inventory-crud`: Extends inventory creation and updating requirements with strict name whitespace sanitization and non-empty content validation.

## Impact
- **New Files:**
  - `backend/tests/unit/test_inventory_schemas.py`
- **Modified Files:**
  - `backend/app/schemas/inventory.py`
- **Dependencies:** None.
- **Breaking Changes:** None. Valid names are unchanged; only invalid whitespace-only or trailing-space inputs are sanitized/rejected.
