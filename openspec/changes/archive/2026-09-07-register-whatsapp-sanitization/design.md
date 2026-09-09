# Design: Register WhatsApp Sanitization & Validation

## Architecture & Context
The TecniDesk frontend provides registration for workshop tenants via `RegisterPage.jsx`. The backend strictly expects pure numeric digits without symbols in `RegisterRequest.contact_whatsapp`. To eliminate friction and 422 errors, sanitization and validation are applied at the presentation boundary before dispatching network requests.

## Decisions & Tradeoffs
1. **Reuse and extend `src/utils/phone.js` vs. standalone file:**
   - *Decision:* Extend `src/utils/phone.js` by adding `normalizeWhatsAppNumber` and `isValidWhatsAppNumber`.
   - *Why:* Keeps mobile phone logic centralized in a single domain utility module, making it easy to test and maintain without fragmenting phone logic.
   - *Tradeoff:* Slightly increases size of `phone.js`, but it's lightweight (pure JS functions, zero external dependencies).

2. **Auto-converting national format (`09XXXXXXXX` -> `5939XXXXXXXX`):**
   - *Decision:* If an Ecuadorian national mobile number is provided (10 digits starting with `09`), automatically transform `09` into `5939`.
   - *Why:* In Ecuador, local workshop administrators instinctively type their mobile number starting with `09`. Forcing them to manually look up country code `593` creates unnecessary onboarding friction.
   - *Tradeoff:* Numbers from other countries without explicit country prefixes are not inferred, but full international numbers (e.g., `+1...`, `+57...`) are stripped of `+` and preserved as pure digits.

3. **Submitting normalized payload vs. mutating input field on change:**
   - *Decision:* Keep user's keystrokes natural in the input field while validating in real-time, and normalize the string when constructing the payload inside `handleSubmit`.
   - *Why:* Mutating input value on every keystroke can disrupt cursor position and frustrate users typing formatting characters.

## File Changes
- **`frontend/src/utils/phone.js`**: Export `normalizeWhatsAppNumber(phone)` and `isValidWhatsAppNumber(phone)`.
- **`frontend/src/pages/RegisterPage.jsx`**:
  - Import `isValidWhatsAppNumber` and `normalizeWhatsAppNumber`.
  - Update `isValid` check to use `isValidWhatsAppNumber(form.contact_whatsapp)`.
  - In `handleSubmit`, send `normalizeWhatsAppNumber(form.contact_whatsapp)`.
- **`frontend/src/tests/utils/phone.test.js`**: Add unit tests for the new functions.
- **`frontend/src/tests/pages/RegisterPage.test.jsx`**: Component integration tests for validation and submission.
