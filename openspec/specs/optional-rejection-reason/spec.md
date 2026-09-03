# Capability: Optional Rejection Reason

## Scenarios

### Scenario 1: Client provides a rejection reason
- **Given** a client who wants to reject a ticket quote
- **When** the client submits a POST request to `/reject` with a JSON payload containing `rejection_reason` (e.g., "Too expensive")
- **Then** the ticket status is updated to `NO_APROBADO`
- **And** the `rejection_reason` is prepended to the ticket's `internal_notes` (e.g., "[MOTIVO DE RECHAZO]: Too expensive").

### Scenario 2: Client rejects without providing a reason
- **Given** a client who wants to reject a ticket quote without additional feedback
- **When** the client submits a POST request to `/reject` with an empty payload or missing `rejection_reason`
- **Then** the ticket status is updated to `NO_APROBADO`
- **And** the ticket's `internal_notes` remain unmodified.
