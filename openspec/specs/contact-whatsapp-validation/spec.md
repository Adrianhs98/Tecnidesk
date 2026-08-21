# Specification: Contact WhatsApp Validation

## Capability
The `RegisterRequest` must validate that the `contact_whatsapp` field contains only numerical digits, enforcing the "formato internacional sin '+'" rule.

## Scenarios

### Scenario 1: Valid international format
**Given** a registration request with a 12-digit numeric `contact_whatsapp` (e.g. "593991234567")
**When** the schema validation is applied
**Then** the request is accepted successfully

### Scenario 2: Request contains a '+' symbol
**Given** a registration request where `contact_whatsapp` starts with a '+' (e.g. "+593991234567")
**When** the schema validation is applied
**Then** the validation fails
**And** returns a clear error message indicating that only numbers are allowed

### Scenario 3: Request contains letters or spaces
**Given** a registration request where `contact_whatsapp` contains spaces or letters (e.g. "593 99 123 4567" or "593abc12345")
**When** the schema validation is applied
**Then** the validation fails
**And** returns a clear error message indicating that only numbers are allowed
