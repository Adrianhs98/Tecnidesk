# Tasks: Ecuadorian Mobile Phone Validation

## 1. Utility Test Suite (TDD - Red)
- [ ] 1.1 Create `frontend/src/tests/utils/phone.test.js` with comprehensive test scenarios (10-digit mobile, international format, formatted with hyphens/spaces, landline rejection, invalid prefix rejection, and empty string handling).

## 2. Utility Implementation (TDD - Green)
- [ ] 2.1 Implement `cleanPhoneNumber` and `isValidMobilePhone` in `frontend/src/utils/phone.js`.
- [ ] 2.2 Run Vitest to verify all tests in `phone.test.js` pass.

## 3. Integration & Component Tests
- [ ] 3.1 Update `frontend/src/features/admin/components/NewTicketModal.jsx` to use `isValidMobilePhone` in form state, sanitize phone in API payload with `cleanPhoneNumber`, and display mobile format hint.
- [ ] 3.2 Create `frontend/src/tests/components/NewTicketModal.test.jsx` testing validation error on invalid phone, successful submit on valid mobile, and payload sanitization.
- [ ] 3.3 Run full test suite (`npm test -- --run`) confirming 100% pass across all test files.
