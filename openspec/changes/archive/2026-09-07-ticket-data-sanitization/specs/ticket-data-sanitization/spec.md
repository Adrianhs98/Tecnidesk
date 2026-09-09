# Specification: Ticket Data Sanitization & Validation

## Capability: ticket-data-sanitization
Ensures core ticket repair order descriptive attributes and optional intake metadata are sanitized and validated at the schema boundary.

### Requirement: Device Brand and Model Sanitization
The schema MUST strip leading and trailing whitespace from `device_brand` and `device_model`, and MUST reject inputs with fewer than 2 non-whitespace characters.

#### Scenario: Stripping leading and trailing whitespace from brand and model
- **Given** a ticket creation payload with `device_brand = "   Apple   "` and `device_model = "   iPhone 13 Pro   "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `device_brand` is stored as `"Apple"`
- **And** `device_model` is stored as `"iPhone 13 Pro"`

#### Scenario: Rejecting whitespace-only device brand
- **Given** a ticket creation payload with `device_brand = "    "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Rejecting whitespace-only device model
- **Given** a ticket creation payload with `device_model = "    "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Rejecting brand or model with fewer than 2 non-whitespace characters
- **Given** a ticket creation payload with `device_brand = " A "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

### Requirement: Issue Description Sanitization
The schema MUST strip leading and trailing whitespace from `issue_description`, and MUST reject inputs with fewer than 5 non-whitespace characters.

#### Scenario: Stripping leading and trailing whitespace from issue description
- **Given** a ticket creation payload with `issue_description = "   Pantalla rota por caída fuerte   "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `issue_description` is stored cleanly as `"Pantalla rota por caída fuerte"`

#### Scenario: Rejecting whitespace-only issue description
- **Given** a ticket creation payload with `issue_description = "       "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Rejecting issue description with fewer than 5 non-whitespace characters
- **Given** a ticket creation payload with `issue_description = "  falla  "[:4]` (" fa ")
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

### Requirement: Ticket Optional Fields Normalization
The schema MUST strip leading and trailing whitespace from optional intake strings (`client_name`, `client_phone`, `internal_notes`), and MUST normalize empty or whitespace-only inputs to `None`.

#### Scenario: Normalizing whitespace-only optional fields to None
- **Given** a ticket creation payload with `client_name = "   "`, `client_phone = "   "`, and `internal_notes = "   "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `client_name` is normalized to `None`
- **And** `client_phone` is normalized to `None`
- **And** `internal_notes` is normalized to `None`

#### Scenario: Preserving trimmed values for valid optional fields
- **Given** a ticket creation payload with `client_name = "  Juan Perez  "` and `client_phone = "  0991234567  "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `client_name` is stored as `"Juan Perez"`
- **And** `client_phone` is stored as `"0991234567"`
