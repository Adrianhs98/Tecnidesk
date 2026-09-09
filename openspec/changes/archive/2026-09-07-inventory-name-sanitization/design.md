# Design: Inventory Item Name Sanitization & Validation

## Architecture & Context
The TecniDesk backend handles catalog items via FastAPI and Pydantic v2 schemas located in `backend/app/schemas/inventory.py`. Data entering through `POST /inventory` and `PATCH /inventory/{id}` is parsed by `InventoryCreate` and `InventoryUpdate`. Sanitizing at the schema validation boundary ensures that database queries, indexing, and UI display receive normalized data without polluting service or database layers.

## Decisions & Tradeoffs
1. **Schema-level `@field_validator` vs. Service-level trimming:**
   - *Decision:* Use Pydantic's `@field_validator("item_name")` in `InventoryCreate` and `InventoryUpdate`.
   - *Why:* Schema validators execute before routing or service logic. This guarantees invalid data is rejected immediately with standard HTTP 422 errors and prevents malformed payloads from ever reaching business logic or the database.
   - *Tradeoff:* Minimal schema overhead, completely standard in FastAPI applications.

2. **Error Message Consistency:**
   - *Decision:* Raise `ValueError("item_name must contain at least 2 non-whitespace characters")` when `len(cleaned) < 2`.
   - *Why:* Pydantic catches `ValueError` inside `@field_validator` and translates it directly into structured `ValidationError` with location `['body', 'item_name']`.

3. **Handling partial updates (`InventoryUpdate`):**
   - *Decision:* If `item_name is None`, return `None` immediately so optional partial updates without `item_name` remain valid.

## File Changes
- **`backend/app/schemas/inventory.py`**:
  - Import `field_validator` from `pydantic`.
  - Add `sanitize_item_name` validator to `InventoryCreate`.
  - Add `sanitize_item_name` validator to `InventoryUpdate`.
- **`backend/tests/unit/test_inventory_schemas.py`**:
  - Add comprehensive unit tests verifying whitespace stripping, rejection of blank/short inputs, and partial update support.
