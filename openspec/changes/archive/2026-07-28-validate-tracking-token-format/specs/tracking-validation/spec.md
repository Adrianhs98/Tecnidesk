# Capability: Tracking Token Validation

## Scenarios

### Scenario 1: Valid UUIDv4 tracking token
- **Given** a valid UUIDv4 tracking token string (e.g., `123e4567-e89b-12d3-a456-426614174000`)
- **When** a client requests a public tracking endpoint (`GET /{tracking_token}`, `POST /{tracking_token}/approve`, `POST /{tracking_token}/reject`)
- **Then** the request passes path parameter validation and proceeds to the service layer.

### Scenario 2: Invalid tracking token format (non-UUID)
- **Given** an invalid tracking token string (e.g., "invalid-token", "123", or a non-UUIDv4 string)
- **When** a client requests a public tracking endpoint
- **Then** the API rejects the request immediately with a validation error (HTTP 422 Unprocessable Entity) without querying the database.
