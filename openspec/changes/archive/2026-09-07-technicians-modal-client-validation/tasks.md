# Tasks: Technicians Modal Client-Side Validation

## 1. Component Tests (TDD - RED Phase)
- [x] 1.1 Create `frontend/src/tests/components/TechniciansModal.test.jsx` with test cases for short/whitespace name blocking, payload sanitization, and inline error banner (RED)
- [x] 1.2 Verify tests fail before implementation

## 2. Implementation (TDD - GREEN Phase)
- [x] 2.1 Update `TechniciansModal.jsx` to introduce `formError` state, validation guards, and inline error banner
- [x] 2.2 Verify `TechniciansModal.test.jsx` passes with `npx vitest run src/tests/components/TechniciansModal.test.jsx` (GREEN)

## 3. Full Verification & Regression
- [x] 3.1 Run full frontend test suite to ensure zero regressions
- [x] 3.2 Verify spec compliance matrix

