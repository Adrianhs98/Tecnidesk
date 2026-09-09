# Specification: Technicians Modal Client-Side Validation

## Capability: technician-client-validation
Ensures technician creation and editing form inputs are validated, sanitized, and accompanied by inline visual feedback within the admin modal.

### Requirement: Technician Full Name Validation
The form MUST prevent submission and display an inline error message if `full_name` contains fewer than 2 non-whitespace characters.

#### Scenario: Blocking submission for whitespace-only name
- **Given** the user inputs `"    "` into the "Nombre Completo" input
- **When** the form is submitted
- **Then** no network request is made
- **And** an inline error banner displays `"El nombre completo debe tener al menos 2 caracteres."`

#### Scenario: Blocking submission for short name
- **Given** the user inputs `" a "` into the "Nombre Completo" input
- **When** the form is submitted
- **Then** no network request is made
- **And** an inline error banner displays `"El nombre completo debe tener al menos 2 caracteres."`

#### Scenario: Trimming full name on submission
- **Given** the user inputs `"   Carlos Mendez   "` into the "Nombre Completo" input
- **When** the form is submitted
- **Then** the payload sent to the backend contains `"full_name": "Carlos Mendez"`

### Requirement: Optional Fields Sanitization
The form MUST trim optional fields (`contact`, `declared_specialty`) and convert empty or whitespace-only values to `null` in the request payload.

#### Scenario: Converting whitespace-only optional fields to null
- **Given** the user inputs `"   "` into "Contacto" and `"   "` into "Especialidad Declarada"
- **And** a valid full name
- **When** the form is submitted
- **Then** the request payload contains `"contact": null` and `"declared_specialty": null`

#### Scenario: Trimming valid optional fields
- **Given** the user inputs `"  0991234567  "` into "Contacto"
- **When** the form is submitted
- **Then** the request payload contains `"contact": "0991234567"`

### Requirement: Inline Error Feedback
When an API request fails, the modal MUST display the error message in an inline error banner rather than a browser alert.

#### Scenario: Displaying API error in inline banner
- **Given** the backend returns an error message `"Error de servidor"`
- **When** the form submission fails
- **Then** an inline banner displays the error text
