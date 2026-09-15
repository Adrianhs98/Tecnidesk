# Proposal: Client Search Query Sanitization & Service Consolidation

## Problem
In `backend/app/routers/clients.py`, the `GET /clients` endpoint:
1. **Redundant inline query logic**: It constructs its own raw SQLAlchemy queries instead of delegating to `ClientService.get_clients`, violating DRY principles and creating divergence with `backend/app/services/client_service.py`.
2. **Missing query length bounds**: The `search` parameter accepts unconstrained query lengths (`Query(None)`), exposing the endpoint to oversized payloads.
3. **Escaping of SQL wildcards**: Raw searches containing `%` or `_` can unintentionally trigger broader LIKE pattern matching.

## Solution
1. **Sanitize and validate in `backend/app/routers/clients.py`**:
   - Add `max_length=100` to `Query(None, max_length=100)`.
   - Delegate query execution to `ClientService.get_clients(shop_id=current_user.shop_id, skip=skip, limit=limit, search=search)`.
2. **Consolidate search sanitization in `backend/app/services/client_service.py`**:
   - Ensure `search` is stripped, whitespace-only values normalize to `None`, and wildcards (`%`, `_`) are safely escaped when building `ilike` filters.
3. **Add unit test coverage**:
   - Add dedicated test cases in `backend/tests/unit/test_search_sanitization.py` and router tests covering max-length validation and whitespace normalization.

## Capabilities
### Modified Capabilities
- `client-listing`: Robust query sanitization, length bounds, and service layer consolidation for customer searches.

## Impact
- **Modified Files:**
  - `backend/app/routers/clients.py`
  - `backend/app/services/client_service.py`
  - `backend/tests/unit/test_search_sanitization.py`
- **Dependencies:** None.
- **Breaking Changes:** None. Fully backward-compatible.
