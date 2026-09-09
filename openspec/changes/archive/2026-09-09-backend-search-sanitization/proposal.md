# Proposal: Backend Search Query Sanitization

## Problem
Currently, several backend endpoints and services accept free-form search query parameters:
- `ticket_service.list_tickets(search=...)` via `GET /tickets`
- `list_inventory(search=..., sku=...)` via `GET /inventory`
- `ClientService.get_clients(search=...)` via `GET /clients`

In all three locations:
1. If a client sends a whitespace-only string (e.g. `search="   "`), Python treats it as truthy (`bool("   ") == True`).
2. The query builder then constructs an SQL filter such as `Customer.full_name.ilike("%   %")` or `Inventory.item_name.ilike("%   %")`.
3. Because normal records do not have sequences of three spaces, this filter returns zero results instead of treating an empty/whitespace query as an unconstrained search (which should return all active records for the shop).
4. Similarly, accidental leading or trailing whitespace (e.g. `search="  Samsung  "`) produces `ilike("%  Samsung  %")`, failing to match `"Samsung Galaxy A54"` due to the padding.
5. In `ticket_service.list_tickets`, attempting `uuid.UUID(search)` with untrimmed whitespace triggers a `ValueError` or unexpected behavior.

## Solution
1. **Sanitize search parameters at service/router boundary**:
   - In `ticket_service.list_tickets`: Strip whitespace from `search`. If the stripped string is empty, normalize to `None`. Use the sanitized string in both the `ilike` patterns and `uuid.UUID` parser.
   - In `backend/app/routers/inventory.py`: Strip whitespace from both `search` and `sku`. Normalize empty/whitespace-only values to `None` before applying `ilike` filters.
   - In `backend/app/services/client_service.py` and `backend/app/routers/clients.py`: Strip whitespace from `search`. Normalize empty/whitespace-only values to `None` before applying `ilike` filters.
2. **Add Unit Tests**:
   - Create `backend/tests/unit/test_search_sanitization.py` verifying:
     - Whitespace-only search strings (`"   "`, `" \t "`) return all items without filtering.
     - Padded search strings (`"  Samsung  "`, `"  display  "`) match correctly by ignoring extraneous leading/trailing spaces.
     - `None` or empty strings (`""`) continue to return all items.

## Capabilities
### New Capabilities
- `backend-search-sanitization`: Automatic normalization and whitespace stripping for search query parameters across tickets, inventory, and client listings.

## Impact
- **New Files:**
  - `backend/tests/unit/test_search_sanitization.py`
- **Modified Files:**
  - `backend/app/services/ticket_service.py`
  - `backend/app/routers/inventory.py`
  - `backend/app/services/client_service.py`
  - `backend/app/routers/clients.py`
- **Dependencies:** None.
- **Breaking Changes:** None. Fixes false-negative zero-result queries caused by whitespace.
