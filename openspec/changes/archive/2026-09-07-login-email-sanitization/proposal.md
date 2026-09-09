# Proposal: Login Email Sanitization & Normalization

## Problem
In `LoginPage.jsx`, when the user submits their login credentials, the form payload is constructed directly as:
```javascript
body: JSON.stringify({ email: form.username, password: form.password })
```
Although `form.username.trim()` is checked in the initial guard, `form.username` is sent without trimming or lowercasing.
This causes two critical usability issues:
1. **Accidental whitespace:** Users on mobile devices or using copy-paste / password autofill often introduce accidental leading or trailing whitespace (e.g. `" admin@taller.com "`). The backend Pydantic schema `LoginRequest` validates with `EmailStr`, which rejects whitespace with a `422 Unprocessable Entity` or fails authentication.
2. **Case sensitivity issues:** Email addresses entered with mixed or uppercase casing (e.g. `"Admin@Taller.com"`) may lead to failed lookups or inconsistent token generation.

## Solution
1. Update `LoginPage.jsx`:
   - Sanitize the email field on submission by applying `.trim().toLowerCase()` to `form.username`.
   - Ensure the sanitized value is dispatched in `POST /auth/login`.
2. Add component test suite in `frontend/src/tests/pages/LoginPage.test.jsx`:
   - Validates that leading and trailing whitespace is stripped before sending to the backend.
   - Validates that email casing is converted to lowercase.
   - Validates that empty or whitespace-only inputs trigger the required field validation error.
   - Validates that successful responses navigate to `/admin` or `/tech` based on user role.

## Capabilities
### New Capabilities
- `login-email-sanitization`: Client-side email trimming and lowercase normalization for authentication requests.

## Impact
- **New Files:**
  - `frontend/src/tests/pages/LoginPage.test.jsx`
- **Modified Files:**
  - `frontend/src/pages/LoginPage.jsx`
- **Dependencies:** None.
- **Breaking Changes:** None. Purely enhances authentication resilience.
