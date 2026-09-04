# Tasks: SLA Overdue Signal and Exception Badge Refinement

## 1. Test Updates (TDD - Red)
- [ ] 1.1 Update `frontend/src/tests/components/AdminTicketCard.test.jsx` with assertions for:
  - `.ticket-card` having the `is-stale` class when SLA is overdue.
  - "Vencido" badge having `title="Tiempo límite de atención superado (SLA vencido)"` and `data-testid="sla-stale-badge"`.
  - "Sin técnico" appearing exactly once when unassigned.

## 2. Styling & Implementation (TDD - Green)
- [ ] 2.1 Add `.badge-exception` and `.ticket-card.is-stale` CSS rules in `frontend/src/App.css`.
- [ ] 2.2 Update `frontend/src/features/admin/components/AdminTicketCard.jsx`:
  - Calculate `stale` with `isTicketStale`.
  - Add `is-stale` conditional class to `.ticket-card`.
  - Add title and testid attributes to the "Vencido" badge.
  - Remove duplicate "Sin técnico" pill from `renderExceptionBadges()`.
- [ ] 2.3 Run Vitest on `AdminTicketCard.test.jsx` to verify all tests pass.

## 3. Verification
- [ ] 3.1 Run the entire test suite (`npm test -- --run`) to confirm 100% pass across all 16 test files.
