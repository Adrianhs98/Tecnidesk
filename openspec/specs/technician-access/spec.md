# Spec: Technician Access Generation

## Requirements

### Requirement: Expose user_id in Technician Responses
The system must include the associated `user_id` in technician response schemas so clients can determine whether a technician has active system credentials.

#### Scenario: Technician with user account
- **Given** an existing technician linked to a user account
- **When** `GET /technicians` or `GET /technicians/metrics` is called
- **Then** the `user_id` field must contain the UUID of the associated user

#### Scenario: Ghost technician
- **Given** an existing technician without a user account
- **When** `GET /technicians` or `GET /technicians/metrics` is called
- **Then** the `user_id` field must be `null`

---

### Requirement: Generate Access for Existing Technician
The system must provide an endpoint to grant system access to an existing active technician who does not yet have credentials.

#### Scenario: Successfully grant access
- **Given** an active technician without an existing `user_id`
- **When** `POST /technicians/{id}/access` is called with `{ "email": "tech@example.com" }` by an admin
- **Then** a new user with role `technician` is created
- **And** credentials are sent to the technician via email
- **And** the technician record is updated with the new `user_id`
- **And** the endpoint returns `200 OK` with the updated technician details

#### Scenario: Duplicate email rejected
- **Given** an email address that already belongs to an existing user
- **When** `POST /technicians/{id}/access` is called with that email
- **Then** the endpoint must return `409 Conflict`
- **And** no duplicate user is created

#### Scenario: Email delivery failure triggers atomic rollback
- **Given** the email dispatch service fails or encounters an error
- **When** `POST /technicians/{id}/access` is called
- **Then** the transaction must rollback completely
- **And** the endpoint must return `502 Bad Gateway`
- **And** no orphaned user or unlinked technician profile remains

#### Scenario: Reject inactive technicians
- **Given** a technician with `is_active = false`
- **When** `POST /technicians/{id}/access` is called
- **Then** the endpoint must return `400 Bad Request`
