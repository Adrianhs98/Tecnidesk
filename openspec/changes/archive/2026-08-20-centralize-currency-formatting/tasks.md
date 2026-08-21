# Tasks: Centralized Currency Formatter

- [x] 1. Utility Implementation & Unit Tests
  - [x] 1.1 Create `frontend/src/tests/utils/currency.test.ts` with test cases covering numbers, numeric strings, zero, null/undefined, and invalid inputs
  - [x] 1.2 Create `frontend/src/utils/currency.js` implementing `formatCurrency` with fallback and symbol options
  - [x] 1.3 Run `vitest run` to confirm all unit tests pass

- [x] 2. Component Integration
  - [x] 2.1 Update `frontend/src/components/shared/ResultCard.jsx` to use `formatCurrency`
  - [x] 2.2 Update `frontend/src/pages/TrackingPortal.jsx` to use `formatCurrency`
  - [x] 2.3 Update `frontend/src/features/admin/components/AdminTicketCard.jsx` to use `formatCurrency`
  - [x] 2.4 Update `frontend/src/features/admin/components/DiagnosticModal.jsx` to use `formatCurrency`
  - [x] 2.5 Update `frontend/src/features/admin/components/InventoryModal.jsx` to use `formatCurrency`
  - [x] 2.6 Update `frontend/src/features/admin/components/PartsSelector.jsx` to use `formatCurrency`
  - [x] 2.7 Update `frontend/src/features/admin/components/TechniciansModal.jsx` to use `formatCurrency`

- [x] 3. Verification & Build Validation
  - [x] 3.1 Run test suite via `npm test`
  - [x] 3.2 Run `npm run build` in `frontend` to ensure zero compilation or import errors
