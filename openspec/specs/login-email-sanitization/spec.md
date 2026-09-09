# Specification: Login Email Sanitization & Normalization

## Capability: login-email-sanitization
Ensures user email input is sanitized and normalized prior to authentication dispatch.

### Requirement: Email Sanitization on Login Submission
The `LoginPage` component MUST sanitize the user-provided email address prior to dispatching `POST /auth/login` by stripping leading/trailing whitespace and converting to lowercase.

#### Scenario: Stripping leading and trailing whitespace
- **Given** the user inputs `"   admin@taller.com   "` into the username/email input
- **And** a valid password
- **When** the user submits the login form
- **Then** the request payload sent to `POST /auth/login` contains `"email": "admin@taller.com"`

#### Scenario: Normalizing uppercase email casing
- **Given** the user inputs `"Admin@Taller.COM"` into the username/email input
- **And** a valid password
- **When** the user submits the login form
- **Then** the request payload sent to `POST /auth/login` contains `"email": "admin@taller.com"`

#### Scenario: Combined whitespace and uppercase normalization
- **Given** the user inputs `"  Carlos.Tech@Taller.COM  "` into the username/email input
- **And** a valid password
- **When** the user submits the login form
- **Then** the request payload sent to `POST /auth/login` contains `"email": "carlos.tech@taller.com"`

### Requirement: Required Field Validation
The `LoginPage` component MUST prevent dispatch and display an error message if the username or password contains only whitespace.

#### Scenario: Whitespace-only username
- **Given** the user inputs `"   "` into the username/email input
- **And** a valid password
- **When** the user clicks "Ingresar"
- **Then** no network request is made
- **And** an error message `"Por favor completa todos los campos."` is displayed
