# Proposal: Validate Tracking Token Format in Public Endpoints

## Why
Currently, the public tracking endpoints (`/api/v1/tracking/{tracking_token}`, `/approve`, and `/reject`) accept any string as `tracking_token` without validating its format prior to querying the database. Since tracking tokens are generated as UUIDv4 strings, invalid or malformed token strings execute unnecessary database queries.

## What
Add input validation to public tracking endpoints so that invalid tracking token formats are rejected early with HTTP status 400 or 422 before querying the database service.

## Capabilities
- `tracking-validation`: Validates UUIDv4 format for tracking tokens in public ticket endpoints.
