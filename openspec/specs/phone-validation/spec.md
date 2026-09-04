# Spec: Mobile Phone Validation

## Capability: phone-validation
Accurate validation and sanitization of Ecuadorian mobile phone numbers for customer intake and WhatsApp communication.

### Requirement: National Mobile Format
The validator MUST accept standard Ecuadorian mobile numbers containing exactly 10 digits starting with `09`.

#### Scenario: Valid 10-digit mobile number
- **Given** a phone number string `"0991234567"`
- **When** `isValidMobilePhone("0991234567")` is called
- **Then** it returns `true`

#### Scenario: Mobile number with spaces or hyphens
- **Given** a formatted phone number `"099 123-4567"`
- **When** `isValidMobilePhone("099 123-4567")` is called
- **Then** it returns `true`
- **And** `cleanPhoneNumber("099 123-4567")` returns `"0991234567"`

### Requirement: International Format
The validator MUST accept Ecuadorian mobile numbers with country code `+593` or `593` followed by a `9` and 8 subscriber digits.

#### Scenario: Valid international number with plus prefix
- **Given** a phone number string `"+593987654321"`
- **When** `isValidMobilePhone("+593987654321")` is called
- **Then** it returns `true`
- **And** `cleanPhoneNumber("+593987654321")` returns `"+593987654321"`

#### Scenario: Valid international number without plus prefix
- **Given** a phone number string `"593987654321"`
- **When** `isValidMobilePhone("593987654321")` is called
- **Then** it returns `true`
- **And** `cleanPhoneNumber("593987654321")` returns `"593987654321"`

### Requirement: Rejection of Invalid or Landline Numbers
The validator MUST reject numbers that do not match mobile patterns, such as provincial landlines, incomplete digits, or wrong network prefixes.

#### Scenario: Rejection of provincial landline
- **Given** a Pichincha/Quito landline number `"022345678"`
- **When** `isValidMobilePhone("022345678")` is called
- **Then** it returns `false`

#### Scenario: Rejection of incomplete number
- **Given** a truncated number `"099123"`
- **When** `isValidMobilePhone("099123")` is called
- **Then** it returns `false`

#### Scenario: Rejection of invalid mobile prefix
- **Given** a number with non-mobile prefix `"0891234567"`
- **When** `isValidMobilePhone("0891234567")` is called
- **Then** it returns `false`

### Requirement: Optional Phone Handling
The validator MUST allow null, undefined, or empty/whitespace-only values when the field is optional.

#### Scenario: Empty or whitespace string
- **Given** an empty string `""` or `"   "`
- **When** `isValidMobilePhone(value)` is called
- **Then** it returns `true`
