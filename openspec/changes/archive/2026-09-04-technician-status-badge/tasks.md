# Tasks: Technician Portal StatusBadge Unification

## 1. Test Updates (TDD - Red)
- [ ] 1.1 In `frontend/src/tests/features/TechnicianPortal.test.jsx`, add an assertion to `TechnicianTicketCard` verifying that a `.ticket-badge` is rendered with `"En revision"` and `"REV"`, and `.tech-status-pill` is no longer present.

## 2. Implementation (TDD - Green)
- [ ] 2.1 Import `<StatusBadge />` in `frontend/src/features/technician/TechnicianTicketCard.jsx`.
- [ ] 2.2 Replace `.tech-status-pill` markup with `<StatusBadge status={ticket.status} />` and remove unused `STATUS_CONFIG` / `statusCfg`.
- [ ] 2.3 Run Vitest to verify `TechnicianPortal.test.jsx` passes.

## 3. Verification
- [ ] 3.1 Run the entire test suite (`npm test -- --run`) to ensure zero regressions across all 16 test files.
