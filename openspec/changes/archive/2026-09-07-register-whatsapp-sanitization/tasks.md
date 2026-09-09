# Tasks: Register WhatsApp Sanitization & Validation

## 1. Phone Utilities & Unit Tests (TDD)
- [x] 1.1 Add unit tests for `normalizeWhatsAppNumber` and `isValidWhatsAppNumber` in `frontend/src/tests/utils/phone.test.js` (RED)
- [x] 1.2 Implement `normalizeWhatsAppNumber` and `isValidWhatsAppNumber` in `frontend/src/utils/phone.js` (GREEN)
- [x] 1.3 Verify tests pass with `npm test -- src/tests/utils/phone.test.js`

## 2. Register Page Integration & Component Tests
- [x] 2.1 Write integration tests in `frontend/src/tests/pages/RegisterPage.test.jsx` verifying sanitized submission and validation states (RED)
- [x] 2.2 Update `frontend/src/pages/RegisterPage.jsx` to validate and normalize WhatsApp number on submit (GREEN)
- [x] 2.3 Verify `RegisterPage.test.jsx` passes with `npm test -- src/tests/pages/RegisterPage.test.jsx`

## 3. Full Verification
- [x] 3.1 Run full frontend test suite to ensure zero regressions
- [x] 3.2 Verify spec compliance matrix
