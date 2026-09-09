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

## Client-side Normalization & Validation

### Requirement: WhatsApp Number Normalization
The frontend utility MUST normalize mobile phone inputs into pure numeric strings suitable for the backend `RegisterRequest` schema:
- Removes spaces, hyphens, parentheses, and leading `+`.
- Converts 10-digit Ecuadorian national mobile numbers starting with `09` to international prefix `5939XXXXXXXX`.
- Retains existing valid international digits (e.g. `5939XXXXXXXX`).

#### Scenario 4: Normalization of national mobile format
**Given** a user input `"0991234567"`
**When** `normalizeWhatsAppNumber("0991234567")` is called
**Then** it returns `"593991234567"`

#### Scenario 5: Normalization of formatted international number with plus
**Given** a user input `"+593 99-123-4567"`
**When** `normalizeWhatsAppNumber("+593 99-123-4567")` is called
**Then** it returns `"593991234567"`

#### Scenario 6: Normalization of clean international number
**Given** a user input `"593991234567"`
**When** `normalizeWhatsAppNumber("593991234567")` is called
**Then** it returns `"593991234567"`

### Requirement: Client-side Validation Helper
The frontend validation helper MUST confirm that the input string normalizes to a valid international mobile number containing between 10 and 20 digits, rejecting landlines or invalid characters.

#### Scenario 7: Valid Ecuadorian mobile numbers
**Given** `"0991234567"` or `"+593991234567"`
**When** `isValidWhatsAppNumber(input)` is called
**Then** it returns `true`

#### Scenario 8: Rejection of invalid inputs
**Given** an invalid input like `"12345"`, `"022345678"` (landline), or `"593abc12345"`
**When** `isValidWhatsAppNumber(input)` is called
**Then** it returns `false`

### Requirement: Frontend Form Integration
The `RegisterPage` form MUST sanitize the phone number and prevent submitting invalid formats.

#### Scenario 9: Sanitized payload submission
**Given** the user inputs `"+593 99 123 4567"` into `contact_whatsapp`
**When** the registration form is submitted
**Then** the request payload sent to `POST /auth/register` contains `"contact_whatsapp": "593991234567"`

#### Scenario 10: Form validation prevents invalid submit
**Given** the user inputs `"022345678"` into `contact_whatsapp`
**When** the user attempts to submit the form
**Then** the submit button is disabled

