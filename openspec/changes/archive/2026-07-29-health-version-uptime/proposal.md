# Proposal: Health Endpoint Version and Uptime Info

## Intent
Enhance the `/health` endpoint of the TecniDesk API to include the current application version and system uptime in seconds, allowing monitoring tools and health checks to inspect operational metrics.

## Scope
- Update `backend/app/routers/health.py` to track service start time.
- Update `/health` response schema/dictionary to include `version` and `uptime_seconds`.
- Add unit test to verify `/health` schema contract.

## Capabilities
- `health`: Service health monitoring endpoint returning operational status, app version, timestamp, and process uptime.

## Risks & Mitigations
- *Risk*: Microsecond precision on uptime might fluctuate across calls.
  *Mitigation*: Return `uptime_seconds` as a float rounded to 2 decimal places.
