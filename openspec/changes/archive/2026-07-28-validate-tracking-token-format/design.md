# Design: Validate Tracking Token Format

## Architecture Decisions

To enforce validation on the `tracking_token` path parameter without adding boilerplate code to every endpoint, we will leverage FastAPI's built-in type validation. By changing the type hint of `tracking_token` from `str` to `uuid.UUID`, FastAPI automatically validates the input format. If an invalid UUID is provided, FastAPI intercepts the request and immediately returns a `422 Unprocessable Entity` response before invoking the path operation function.

We will then cast the `UUID` object back to a `str` when passing it down to the `ticket_service`, as the database layer currently expects a string for the query.

## File Changes

- `backend/app/api/v1/endpoints/tracking.py`:
  - Import `UUID` from the standard `uuid` module.
  - In `get_public_ticket`, change the parameter type to `tracking_token: UUID`.
  - In `approve_ticket`, change the parameter type to `tracking_token: UUID`.
  - In `reject_ticket`, change the parameter type to `tracking_token: UUID`.
  - Cast `tracking_token` to string (`str(tracking_token)`) when calling `ticket_service` methods.

## Alternatives Considered

- **Using a custom dependency or middleware:** Rejected because it adds unnecessary complexity. FastAPI's native type validation is idiomatic and sufficient.
- **Using FastAPI `Path(regex=...)` with string type:** This would keep the parameter as a string, avoiding the cast to `str`. However, `uuid.UUID` is more semantically correct, provides stronger guarantees, and produces better OpenAPI schema documentation. Thus, casting it to `str(tracking_token)` at the service boundary is a worthwhile trade-off.
