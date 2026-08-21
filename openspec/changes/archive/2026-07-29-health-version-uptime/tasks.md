# Tasks: Health Endpoint Version and Uptime Info

- [ ] 1. Update `backend/app/routers/health.py`
  - [ ] 1.1 Add `import time` and initialize `START_TIME = time.time()`.
  - [ ] 1.2 Return `version` and `uptime_seconds` in `health_check()`.
- [ ] 2. Add test coverage
  - [ ] 2.1 Create or update `backend/tests/test_health.py` to test `/health` payload.
- [ ] 3. Verification
  - [ ] 3.1 Execute pytest to verify health check functionality.
