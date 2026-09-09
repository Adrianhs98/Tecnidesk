# Design: Login Email Sanitization & Normalization

## Architecture & Context
The authentication flow starts in `frontend/src/pages/LoginPage.jsx`. Credentials are transmitted via HTTP POST to `/auth/login`. Modern browsers and mobile keyboards frequently introduce trailing spaces during autocomplete or password-manager fills, and users may type email addresses in title or uppercase. Handling sanitization at the presentation layer guarantees clean inputs for the API.

## Decisions & Tradeoffs
1. **Sanitize upon submission vs. onChange:**
   - *Decision:* Keep the input state natural while typing and sanitize inside `handleSubmit` when constructing the request payload.
   - *Why:* Normalizing or lowercasing while typing can cause cursor jumps and jarring visual effects on mobile keyboards.
   - *Tradeoff:* User sees what they typed, while the server receives the clean normalized string.

2. **Sanitization rule:**
   - *Decision:* Apply `form.username.trim().toLowerCase()`.
   - *Why:* Email addresses are RFC 5321 case-insensitive for domain names and standard convention for mailboxes. Trimming prevents Pydantic's `EmailStr` format rejections.

## File Changes
- **`frontend/src/pages/LoginPage.jsx`**:
  - In `handleSubmit`, assign `const email = form.username.trim().toLowerCase();`
  - Pass `email` in the fetch request body.
- **`frontend/src/tests/pages/LoginPage.test.jsx`**:
  - Add comprehensive component tests covering whitespace trimming, lowercase conversion, empty field validation, and successful login navigation.
