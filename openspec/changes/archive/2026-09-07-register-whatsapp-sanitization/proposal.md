# Proposal: Register WhatsApp Sanitization & Validation

## Problem
In `RegisterPage.jsx`, client-side validation for `contact_whatsapp` only verifies `form.contact_whatsapp.trim().length >= 10`. It does not strip formatting characters (spaces, dashes, parentheses, leading `+`) nor does it normalize standard Ecuadorian national mobile numbers (`09XXXXXXXX`) to the international format (`5939XXXXXXXX`).

When an administrator inputs a phone in common formats such as `+593 99 123 4567` or `0991234567`, the frontend sends the unsanitized string to `POST /auth/register`. The backend schema `RegisterRequest` enforces `pattern=r"^\d+$"` (digits only without `+`), resulting in an immediate `422 Unprocessable Entity` response and a broken onboarding experience.

## Solution
1. Add utility functions in `frontend/src/utils/phone.js`:
   - `normalizeWhatsAppNumber(phone)`: Strips all non-digit characters, removes leading `+`, and converts national Ecuadorian mobile numbers (`09XXXXXXXX`, 10 digits) to international format (`5939XXXXXXXX`).
   - `isValidWhatsAppNumber(phone)`: Checks if the phone can be normalized into a valid digits-only international number (10 to 15 digits).
2. Integrate into `frontend/src/pages/RegisterPage.jsx`:
   - Enforce `isValidWhatsAppNumber(form.contact_whatsapp)` in the `isValid` form check.
   - Automatically normalize `contact_whatsapp` before dispatching the payload to `POST /auth/register`.
   - Provide an informative format helper / error feedback to prevent invalid submissions.
3. Test Coverage:
   - Unit tests for new utilities in `frontend/src/tests/utils/phone.test.js`.
   - Component tests in `frontend/src/tests/pages/RegisterPage.test.jsx` asserting validation state, error handling, and normalized payload transmission.

## Capabilities
### Modified Capabilities
- `contact-whatsapp-validation`: Extends WhatsApp validation and sanitization into the frontend registration flow.

## Impact
- **New Files:**
  - `frontend/src/tests/pages/RegisterPage.test.jsx`
- **Modified Files:**
  - `frontend/src/utils/phone.js`
  - `frontend/src/tests/utils/phone.test.js`
  - `frontend/src/pages/RegisterPage.jsx`
- **Dependencies:** None.
- **Breaking Changes:** None. The backend already requires pure digits without `+`; the frontend now guarantees compliance.
