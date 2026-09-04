# Proposal: Ecuadorian Mobile Phone Validation

## Problem
In `NewTicketModal.jsx`, customer phone validation relies on a generic regex (`/^\+?[0-9]{7,15}$/`). This permits invalid or landline numbers (e.g., `1234567`, `022345678`) to be stored in the database. When tickets transition to `LISTO_PARA_RETIRAR` or `ESPERANDO_APROBACION`, the Smart Action CTA builds WhatsApp click-to-chat links (`https://wa.me/${phone}`) that fail or open invalid chats.

Furthermore, user input often contains common formatting artifacts (spaces, dashes, country prefixes) that are not sanitized before submission, and the form lacks inline feedback explaining the required mobile format.

## Solution
1. Create a centralized validation and sanitization utility in `frontend/src/utils/phone.js`:
   - `isValidMobilePhone(phone)`: Validates Ecuadorian mobile numbers (national format `09XXXXXXXX` with 10 digits, or international `+5939XXXXXXXX` / `5939XXXXXXXX`). Returns `true` for empty values when optional.
   - `cleanPhoneNumber(phone)`: Normalizes input by removing whitespace, hyphens, and parentheses.
2. Integrate the validator into `NewTicketModal.jsx` to replace the naive regex, enforce accurate validation on save, and display a helpful format hint (`"Formato: 09XXXXXXXX o +5939XXXXXXXX"`).
3. Cover the capability with unit tests in `frontend/src/tests/utils/phone.test.js` and `frontend/src/tests/components/NewTicketModal.test.jsx`.

## Capabilities
### New Capabilities
- `phone-validation`: Accurate validation and sanitization of Ecuadorian mobile phone numbers for customer intake and WhatsApp communication.

## Impact
- **New Files:**
  - `frontend/src/utils/phone.js`
  - `frontend/src/tests/utils/phone.test.js`
  - `frontend/src/tests/components/NewTicketModal.test.jsx`
- **Modified Files:**
  - `frontend/src/features/admin/components/NewTicketModal.jsx`
- **Dependencies:** None. Pure JavaScript regex and string utilities.
- **Breaking Changes:** None. Phone remains optional; only non-empty inputs are strictly validated.
