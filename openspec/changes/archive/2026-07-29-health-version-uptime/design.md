# Design: Health Endpoint Version and Uptime Info

## Architecture & File Changes
- `backend/app/routers/health.py`:
  - Record `START_TIME = time.time()` at module initialization.
  - Calculate `uptime_seconds = round(time.time() - START_TIME, 2)`.
  - Include `"version": "1.0.0"` and `"uptime_seconds": uptime_seconds` in `health_check()` response.
- `backend/tests/test_health.py`:
  - Add test case verifying presence and type of `version` and `uptime_seconds`.

## Decisions & Tradeoffs
- **Module-level START_TIME**: Simple and efficient, doesn't require passing FastAPI application instance to router dependencies.
- **2-Decimal Rounding**: Clean representation of seconds without excessive floating-point noise.
