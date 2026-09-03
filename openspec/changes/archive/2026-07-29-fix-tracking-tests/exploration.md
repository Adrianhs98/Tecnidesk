# Exploration: Fix Tracking Tests

## 1. Context and Findings
The test file `backend/tests/unit/test_tracking_validation.py` contains 3 failing tests:
- `test_invalid_tracking_token_returns_422`
- `test_invalid_tracking_token_approve_returns_422`
- `test_invalid_tracking_token_reject_returns_422`

All 3 tests make requests to endpoints starting with `/api/v1/tracking/invalid-token-123`.
They expect a `422 Unprocessable Entity` response but are receiving `404 Not Found`.

## 2. Root Cause
The `404 Not Found` response is due to a mismatch in the URL path:
1. In `backend/app/main.py`, the router is mounted without a prefix:
   ```python
   # RUTAS PÚBLICAS — El antiguo /track fue reemplazado por /tracking (app/api/v1/)
   from app.api.v1.api import api_router as tracking_api_router
   app.include_router(tracking_api_router)
   ```
2. In `backend/app/api/v1/api.py`, the `tracking_api_router` mounts the tracking endpoints at `/tracking`:
   ```python
   api_router.include_router(tracking.router, prefix="/tracking", tags=["Tracking Público"])
   ```
3. Therefore, the actual URL of the endpoints is `/tracking/{tracking_token}` (and its sub-routes), not `/api/v1/tracking/{tracking_token}`.

Because the tests are calling `/api/v1/tracking/...`, FastAPI is unable to match the route, resulting in a `404 Not Found`.

FastAPI's default behavior for path parameters (e.g. `/{tracking_token}` where `tracking_token: UUID`) is to match any string at the Starlette routing level, and then parse it using Pydantic. If Pydantic fails to parse the string as a UUID, it raises a `ValidationError`, which FastAPI maps to a `422 Unprocessable Entity`. 

## 3. Comparison of Approaches

We have two options to fix this issue:

### Option A: Update the tests to use the correct URL
- Change the URL in `backend/tests/unit/test_tracking_validation.py` from `/api/v1/tracking/...` to `/tracking/...`.
- **Pros**: Matches the actual current implementation and intended public URL (as implied by the comment `# RUTAS PÚBLICAS — El antiguo /track fue reemplazado por /tracking`).
- **Cons**: None, this reflects the reality of the app.

### Option B: Mount the router at `/api/v1`
- Update `backend/app/main.py` to include the router with `prefix="/api/v1"`.
- **Pros**: Groups all v1 APIs under `/api/v1`.
- **Cons**: Disagrees with the explicit `main.py` comment that states it was moved to `/tracking`. Since these are public-facing tracking links (typically used in SMS/Emails), `/tracking/...` is much more user-friendly than `/api/v1/tracking/...`.

## 4. Conclusion
The most logical and correct fix is **Option A**. The tests should be updated to request `/tracking/...` instead of `/api/v1/tracking/...` because the public-facing URL is intended to be shorter and cleaner.
