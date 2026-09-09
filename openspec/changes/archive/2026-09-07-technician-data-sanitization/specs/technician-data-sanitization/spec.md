# Specification: Technician Data Sanitization & Validation

## Capability: technician-data-sanitization
Ensures technician personal details and attributes are sanitized and validated at the schema boundary.

### Requirement: Technician Full Name Sanitization & Validation
The schema MUST strip leading and trailing whitespace from `full_name`, and MUST reject inputs with fewer than 2 non-whitespace characters.

#### Scenario: Stripping leading and trailing whitespace on create
- **Given** a technician creation payload with `full_name = "   Carlos Mendez   "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `full_name` is stored cleanly as `"Carlos Mendez"`

#### Scenario: Rejecting whitespace-only full name on create
- **Given** a technician creation payload with `full_name = "    "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Rejecting single-character full name on create
- **Given** a technician creation payload with `full_name = " c "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Stripping leading and trailing whitespace on update
- **Given** a technician update payload with `full_name = "   Carlos M.   "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `full_name` is cleaned to `"Carlos M."`

#### Scenario: Rejecting whitespace-only full name on update
- **Given** a technician update payload with `full_name = "   "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Allowing None full name on partial update
- **Given** a technician update payload with `full_name = None` and `declared_specialty = "Apple"`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `full_name` remains `None`

### Requirement: Optional Fields Sanitization
The schema MUST strip leading and trailing whitespace from `contact` and `declared_specialty`, and MUST normalize empty or whitespace-only inputs to `None`.

#### Scenario: Normalizing whitespace-only contact to None
- **Given** a technician creation or update payload with `contact = "    "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `contact` is normalized to `None`

#### Scenario: Normalizing whitespace-only declared_specialty to None
- **Given** a technician creation or update payload with `declared_specialty = "   "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `declared_specialty` is normalized to `None`

#### Scenario: Stripping whitespace on valid optional values
- **Given** `contact = "  0991234567  "` and `declared_specialty = "  Microsoldadura  "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `contact` is `"0991234567"`
- **And** `declared_specialty` is `"Microsoldadura"`
