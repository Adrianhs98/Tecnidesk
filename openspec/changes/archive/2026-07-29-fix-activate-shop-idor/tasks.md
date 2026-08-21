# Tasks: fix-activate-shop-idor

- [x] 1. Add `superadmin_api_key` configuration setting
  - [x] 1.1 Update `app/config.py` with `superadmin_api_key: str = "change-me-superadmin-secret-key"`
  - [x] 1.2 Update `backend/.env.example` to document `SUPERADMIN_API_KEY`

- [x] 2. Implement `superadmin_key_guard` dependency
  - [x] 2.1 Import `secrets` and `APIKeyHeader` in `app/core/dependencies.py`
  - [x] 2.2 Define `superadmin_key_guard` verifying `X-Superadmin-Key` header with `secrets.compare_digest`
  - [x] 2.3 Raise 401 if header is missing, 403 if key is invalid

- [x] 3. Protect `POST /tickets/admin/activate-shop` endpoint
  - [x] 3.1 Import `superadmin_key_guard` in `app/routers/tickets.py`
  - [x] 3.2 Update `activate_shop` router function signature to use `Depends(superadmin_key_guard)`

- [x] 4. Verify implementation
  - [x] 4.1 Write pytest integration tests for 401, 403, and 200 responses on `/tickets/admin/activate-shop`
  - [x] 4.2 Run test suite to verify 100% compliance
