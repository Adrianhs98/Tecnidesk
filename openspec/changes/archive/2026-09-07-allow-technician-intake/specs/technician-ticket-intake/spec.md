# Specification: Technician Ticket Intake Policy

## Capability: technician-ticket-intake
Provides per-workshop authorization controls allowing technicians to register new repair tickets according to shop owner configuration.

### Requirement: Workshop Setting for Technician Intake
The system MUST store and manage a boolean configuration `allow_technician_intake` on the `Shop` entity, defaulting to `False`.

#### Scenario: Default setting for new shops
- **Given** a new shop onboarding
- **When** the shop record is created
- **Then** `allow_technician_intake` defaults to `False`.

#### Scenario: Admin updates shop settings
- **Given** an authenticated user with role `admin`
- **When** `PATCH /shops/settings` is called with `{ "allow_technician_intake": true }`
- **Then** the shop record is updated
- **And** the endpoint returns HTTP 200 with `{ "allow_technician_intake": true }`.

#### Scenario: Non-admin is rejected from updating shop settings
- **Given** an authenticated user with role `technician`
- **When** `PATCH /shops/settings` is called
- **Then** the system returns HTTP 403 Forbidden.

### Requirement: Ticket Creation Authorization
The system MUST validate user permissions on `POST /tickets` using the `verify_can_create_ticket` guard.

#### Scenario: Admin creates ticket regardless of flag
- **Given** an authenticated user with role `admin`
- **And** a shop with `allow_technician_intake = False`
- **When** `POST /tickets` is invoked with valid ticket payload
- **Then** the ticket is created successfully with HTTP 201 Created.

#### Scenario: Technician creates ticket when flag is enabled
- **Given** an authenticated user with role `technician`
- **And** their shop has `allow_technician_intake = True`
- **When** `POST /tickets` is invoked with valid ticket payload
- **Then** the ticket is created successfully with HTTP 201 Created
- **And** the technician is recorded as the actor in initial ticket status history.

#### Scenario: Technician creates ticket when flag is disabled
- **Given** an authenticated user with role `technician`
- **And** their shop has `allow_technician_intake = False`
- **When** `POST /tickets` is invoked
- **Then** the system returns HTTP 403 Forbidden.

### Requirement: Technician Profile Capability Flag
The system MUST include `allow_technician_intake` in `GET /technicians/me` response.

#### Scenario: Fetching technician profile
- **Given** an authenticated technician user
- **When** `GET /technicians/me` is called
- **Then** the response includes `allow_technician_intake: bool` reflecting their shop's configuration.

### Requirement: Frontend Intake Presentation
The technician dashboard MUST conditionally render the device intake action based on `allow_technician_intake`.

#### Scenario: Intake button visibility for technicians
- **Given** a technician logged into their dashboard
- **When** `allow_technician_intake` is `True`
- **Then** the "Ingresar Equipo" action button is visible and opens `NewTicketModal`.
- **When** `allow_technician_intake` is `False`
- **Then** the "Ingresar Equipo" action button is not rendered.
