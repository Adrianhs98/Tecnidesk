# Tasks: Login Email Sanitization & Normalization

## 1. Component Tests (TDD - RED Phase)
- [x] 1.1 Create `frontend/src/tests/pages/LoginPage.test.jsx` with test cases for email trimming, lowercasing, and required validations (RED)
- [x] 1.2 Verify tests fail before implementation

## 2. Implementation (TDD - GREEN Phase)
- [x] 2.1 Update `handleSubmit` in `frontend/src/pages/LoginPage.jsx` to normalize email with `.trim().toLowerCase()`
- [x] 2.2 Verify `LoginPage.test.jsx` passes with `npx vitest run src/tests/pages/LoginPage.test.jsx` (GREEN)

## 3. Full Verification & Regression
- [x] 3.1 Run full frontend test suite to ensure zero regressions
- [x] 3.2 Verify spec compliance matrix
