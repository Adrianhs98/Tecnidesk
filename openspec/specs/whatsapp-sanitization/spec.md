# Capability: WhatsApp Number Sanitization

## Scenarios

### Scenario 1: WhatsApp number contains formatting characters
- **Given** a shop with a WhatsApp number containing non-digit characters (e.g., `+593 99 123-4567` or `(593) 991234567`)
- **When** the public tracking API returns the ticket information
- **Then** the `contact_whatsapp` field in the response contains only numeric digits (e.g., `593991234567`).

### Scenario 2: WhatsApp number is not configured
- **Given** a shop with no WhatsApp number configured, or an empty string
- **When** the public tracking API returns the ticket information
- **Then** the `contact_whatsapp` field in the response remains `null`.
