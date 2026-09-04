# Tasks: Unified StatusBadge Component

## 1. Test Suite (TDD - Red)
- [ ] 1.1 Create test file `frontend/src/tests/components/StatusBadge.test.jsx` covering known statuses, fallback for unknown status, and `showIcon={false}` prop.

## 2. Component Implementation (Green)
- [ ] 2.1 Implement `frontend/src/components/shared/StatusBadge.jsx` consuming `STATUS_CONFIG` from `src/utils/constants.js`.
- [ ] 2.2 Run Vitest to verify all tests pass in `StatusBadge.test.jsx`.

## 3. Integration & Refactor
- [ ] 3.1 Import `<StatusBadge />` in `frontend/src/features/admin/components/AdminTicketCard.jsx` and replace the inline badge markup.
- [ ] 3.2 Run the entire frontend test suite to ensure 100% compliance across all 13 test files.
