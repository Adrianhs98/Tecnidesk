# Design: Ecuadorian Mobile Phone Validation

## Architecture Overview
The phone validation logic is placed in `frontend/src/utils/phone.js` as a set of pure, standalone utility functions with zero external dependencies.

It serves two primary purposes:
1. Validating whether an input string represents a valid Ecuadorian cellular number (either in national `09XXXXXXXX` format or international `+5939XXXXXXXX` / `5939XXXXXXXX` format).
2. Sanitizing formatting punctuation (spaces, dashes, parentheses) before passing the number to the backend API or generating WhatsApp links.

## Function Contracts

```javascript
/**
 * Removes spaces, dashes, parentheses and periods from a phone string,
 * preserving a leading '+' if present.
 *
 * @param {string} phone
 * @returns {string}
 */
export function cleanPhoneNumber(phone)

/**
 * Validates whether the given phone string matches Ecuadorian mobile formats.
 * Returns true if the phone is empty or undefined (when optional).
 *
 * @param {string} phone
 * @returns {boolean}
 */
export function isValidMobilePhone(phone)
```

## Decisions & Tradeoffs

### Decision 1: Regex-based utility over `libphonenumber-js`
- **Rationale:** `libphonenumber-js` or `google-libphonenumber` adds 140KB+ to the client bundle. The Ecuadorian cellular number format is strict and unambiguous (`09` + 8 digits, or `+5939` + 8 digits). A focused regex achieves 100% accuracy with 0 overhead.
- **Tradeoff:** Does not validate all 200+ countries, which is an intentional architectural tradeoff since TecniDesk is explicitly localized for Ecuadorian workshops.

### Decision 2: Sanitization on submit rather than aggressive input masking
- **Rationale:** Strict input masks (`___-___-____`) often break copy-paste workflows and mobile keyboard auto-completion. Allowing standard punctuation (`099 123 4567` or `099-123-4567`), validating it cleanly, and sanitizing before the API payload gives the best counter-operator UX.

## File Changes
- `frontend/src/utils/phone.js` (New)
- `frontend/src/tests/utils/phone.test.js` (New)
- `frontend/src/features/admin/components/NewTicketModal.jsx` (Modified to use `isValidMobilePhone` and `cleanPhoneNumber`)
- `frontend/src/tests/components/NewTicketModal.test.jsx` (New)
