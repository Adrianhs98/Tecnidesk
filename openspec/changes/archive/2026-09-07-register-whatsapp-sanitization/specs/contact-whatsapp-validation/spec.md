# Specification Delta: Contact WhatsApp Validation

## Capability: contact-whatsapp-validation
Extends WhatsApp validation and sanitization into the client-side registration flow.

### Requirement: WhatsApp Number Normalization
The utility MUST normalize mobile phone inputs into pure numeric strings suitable for the backend `RegisterRequest` schema:
- Removes spaces, hyphens, parentheses, and leading `+`.
- Converts 10-digit Ecuadorian national mobile numbers starting with `09` to international prefix `5939XXXXXXXX`.
- Retains existing valid international digits (e.g. `5939XXXXXXXX`).

#### Scenario: Normalization of national mobile format
- **Given** a user input `"0991234567"`
- **When** `normalizeWhatsAppNumber("0991234567")` is called
- **Then** it returns `"593991234567"`

#### Scenario: Normalization of formatted international number with plus
- **Given** a user input `"+593 99-123-4567"`
- **When** `normalizeWhatsAppNumber("+593 99-123-4567")` is called
- **Then** it returns `"593991234567"`

#### Scenario: Normalization of clean international number
- **Given** a user input `"593991234567"`
- **When** `normalizeWhatsAppNumber("593991234567")` is called
- **Then** it returns `"593991234567"`

### Requirement: WhatsApp Number Validation
The validation helper MUST confirm that the input string normalizes to a valid international mobile number containing between 10 and 15 digits.

#### Scenario: Valid Ecuadorian mobile numbers
- **Given** `"0991234567"` or `"+593991234567"`
- **When** `isValidWhatsAppNumber(input)` is called
- **Then** it returns `true`

#### Scenario: Rejection of invalid inputs
- **Given** an invalid input like `"12345"`, `"022345678"` (landline), or `"593abc12345"`
- **When** `isValidWhatsAppNumber(input)` is called
- **Then** it returns `false`

### Requirement: Frontend Form Integration
The `RegisterPage` form MUST sanitize the phone number and prevent submitting invalid formats.

#### Scenario: Sanitized payload submission
- **Given** the user inputs `"+593 99 123 4567"` into `contact_whatsapp`
- **When** the registration form is submitted
- **Then** the request payload sent to `POST /auth/register` contains `"contact_whatsapp": "593991234567"`

#### Scenario: Form validation prevents invalid submit
- **Given** the user inputs `"022345678"` into `contact_whatsapp`
- **When** the user attempts to submit the form
- **Then** the submit button is disabled or submission is halted with a clear error message
