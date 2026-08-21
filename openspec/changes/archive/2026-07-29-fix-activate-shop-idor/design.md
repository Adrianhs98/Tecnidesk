# Design: fix-activate-shop-idor

## Architectural Decisions

### Decision 1: Platform API Key Header Guard vs JWT Roles
- **Choice**: Use a custom `superadmin_key_guard` dependency reading the `X-Superadmin-Key` header.
- **Rationale**: The database schema does not have a `super_admin` role or a system tenant (`shop_id`). Creating a new user role requires schema migrations and complex tenant checks. A dedicated platform header provides clean separation between tenant space and operator actions.

### Decision 2: Constant-time String Comparison
- **Choice**: Use Python's `secrets.compare_digest(provided_key, settings.superadmin_api_key)`.
- **Rationale**: Standard string equality (`==`) leaks timing information based on how many initial characters match. `secrets.compare_digest` executes in constant time, preventing timing attacks.

---

## File Changes & Modifications

### 1. `backend/app/config.py`
- Add `superadmin_api_key: str = "change-me-superadmin-secret-key"` to `Settings`.

### 2. `backend/app/core/dependencies.py`
- Import `secrets` and `APIKeyHeader`.
- Define `superadmin_key_scheme = APIKeyHeader(name="X-Superadmin-Key", auto_error=False)`.
- Define `superadmin_key_guard(key: str | None = Depends(superadmin_key_scheme))`:
  - If `key` is missing -> `HTTP 401 Unauthorized` ("Se requiere la cabecera X-Superadmin-Key").
  - If `not secrets.compare_digest(key, settings.superadmin_api_key)` -> `HTTP 403 Forbidden` ("Clave de superadministrador inválida").
  - Return `key`.

### 3. `backend/app/routers/tickets.py`
- Import `superadmin_key_guard` from `app.core.dependencies`.
- Update `activate_shop` signature: replace `current_user: User = Depends(get_current_user)` with `_: str = Depends(superadmin_key_guard)`.

### 4. `backend/.env.example`
- Add `SUPERADMIN_API_KEY=change-me-superadmin-secret-key`.

---

## Verification Plan

### Manual / Integration Tests
1. Call `POST /tickets/admin/activate-shop` without headers -> Expected `401`.
2. Call `POST /tickets/admin/activate-shop` with `X-Superadmin-Key: wrongkey` -> Expected `403`.
3. Call `POST /tickets/admin/activate-shop` with `X-Superadmin-Key: change-me-superadmin-secret-key` -> Expected `200` & subscription updated.
