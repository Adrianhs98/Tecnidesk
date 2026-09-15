# Design: Client Search Query Sanitization & Service Layer Consolidation

## Architecture Decisions

### Decision 1: Delegate Router Logic to `ClientService`
- **Context**: `backend/app/routers/clients.py` previously executed inline SQLAlchemy statements instead of using `ClientService`.
- **Decision**: Delegate all database queries in `GET /clients` to `ClientService(db).get_clients(shop_id=current_user.shop_id, skip=skip, limit=limit, search=search)`.
- **Trade-off**: Cleaner separation of concerns; keeps the router thin and responsible solely for HTTP parameters/response serialization.

### Decision 2: Max Length Enforcement at FastAPI Query Boundary
- **Context**: Search parameter had no max_length bound.
- **Decision**: Update router definition to `search: Optional[str] = Query(None, max_length=100)`.
- **Trade-off**: Fast rejection with 422 before touching the database or running string transformations.

### Decision 3: Safe ILIKE Escaping in `ClientService`
- **Context**: Direct interpolation `f"%{search}%"` interprets `%` and `_` as SQL LIKE wildcards.
- **Decision**: Sanitize search term by stripping whitespace. If non-empty, escape `\\`, `%` and `_` characters with backslashes before wrapping with `%...%`.
- **Trade-off**: Prevents unintended wildcard matches without adding complex parsing.

## File Changes
1. `backend/app/routers/clients.py`:
   - Add `max_length=100` to `search` Query parameter.
   - Replace inline database operations with `ClientService(db).get_clients(...)`.
2. `backend/app/services/client_service.py`:
   - Sanitize search input (strip, check if non-empty).
   - Escape `%` and `_` wildcards before forming `ilike` query.
3. `backend/tests/unit/test_search_sanitization.py`:
   - Add test scenarios verifying wildcard escaping, whitespace normalization, and max length bounds on `ClientService` and router.
