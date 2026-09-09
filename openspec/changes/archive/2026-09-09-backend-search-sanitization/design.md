# Design: Backend Search Query Sanitization

## Architecture & Context
In TecniDesk, workshop operators and technicians frequently filter records through list endpoints:
- `GET /tickets` (`ticket_service.list_tickets`)
- `GET /inventory` (`inventory.list_inventory`)
- `GET /clients` (`client_service.ClientService.get_clients` and `clients.get_clients`)

Currently, passing a string composed entirely of whitespace causes the application to construct `ilike("%   %")` clauses, filtering out all legitimate records. Additionally, accidental leading or trailing whitespace causes partial search terms to miss target rows.

## Decisions & Tradeoffs
1. **Service and Router Boundary Normalization:**
   - *Decision:* At the beginning of `list_tickets`, `list_inventory`, and `get_clients`, normalize `search`:
     ```python
     search = search.strip() if search else None
     if search == "":
         search = None
     ```
   - *Why:* Keeps query construction clean and uniform. If `search` is `None` (either originally or after trimming), no search filter is attached to SQLAlchemy `select()`, returning all records matching shop scope and pagination.

2. **Accidental Whitespace in UUID Searches:**
   - *Decision:* In `ticket_service.list_tickets`, `uuid.UUID(search)` is executed on the already-trimmed `search` string.
   - *Why:* Users or clipboard operations often include a trailing space when pasting a ticket UUID into the search bar. Stripping ensures the UUID parser recognizes valid UUIDs instead of falling back to text ILIKE.

3. **SKU Sanitization in Inventory:**
   - *Decision:* Apply the same stripping and `None`-normalization to `sku` in `list_inventory`.
   - *Why:* Prevents blank SKU filters from returning empty lists when an empty SKU parameter is sent by frontend clients.

## File Changes
- **`backend/app/services/ticket_service.py`**:
  - Normalize `search` parameter at top of `list_tickets`.
- **`backend/app/routers/inventory.py`**:
  - Normalize `search` and `sku` parameters in `list_inventory`.
- **`backend/app/services/client_service.py`**:
  - Normalize `search` parameter in `ClientService.get_clients`.
- **`backend/app/routers/clients.py`**:
  - Normalize `search` parameter in `get_clients`.
- **`backend/tests/unit/test_search_sanitization.py`**:
  - Add test suite covering whitespace-only search, padded search terms, empty string search, and UUID search across all three domains.
