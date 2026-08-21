# Spec: Customer PII Privacy

## Requirements

### Requirement: Mask Phone Numbers from Prefix
The system must keep only the first two characters of a phone number visible and replace all subsequent digits with "x".

#### Scenario: Phone number masking from 3rd character
- **Given** a customer phone number (e.g., "0991234567" or "+5491112345678")
- **When** it is rendered through the phone masking utility
- **Then** only the first two characters should remain visible (e.g., "09xxxxxxxx" or "+5xxxxxxxxxxxxx")

### Requirement: Mask Emails on Dashboard Views
The system must replace characters in the local part of an email address with "x", preserving the domain part.

#### Scenario: Email address username masking
- **Given** a customer email address (e.g., "cliente.apellido@gmail.com")
- **When** it is rendered through the email masking utility
- **Then** the local part should be masked while keeping the domain visible (e.g., "clxxxxxxo@gmail.com")

### Requirement: Interactive Reveal Toggle in Detail Modal
The system must render customer contact details masked by default inside the ticket detail modal, providing an eye icon button to toggle revealing the full unmasked data.

#### Scenario: Detail modal opens masked by default
- **Given** a technician opens the ticket detail modal
- **When** the modal renders the customer section
- **Then** the phone number and email must be displayed in their masked format by default

#### Scenario: Clicking eye toggle reveals raw PII
- **Given** the ticket detail modal is open with masked customer data
- **When** the technician clicks the reveal (eye) toggle button
- **Then** the raw, unmasked phone number and email must be displayed immediately
- **And** the eye button icon should change to indicate an un-reveal action (EyeOff)
