# Proposal: SLA Overdue Signal and Exception Badge Refinement in AdminTicketCard

## Problem
In `AdminTicketCard.jsx`, SLA expiration and exception indicators suffer from several issues:
1. When a ticket is overdue (`isTicketStale`), the "Vencido" badge renders without a container-level alert style (unlike `KanbanTicketCard` which applies `kanban-card-danger is-stale` and `TechnicianTicketCard` which applies `is-overdue`). This prevents operators from spotting critical delays when scanning the list view.
2. The "Vencido" badge lacks an accessible title/tooltip (`title="Tiempo límite de atención superado (SLA vencido)"`) explaining the SLA context.
3. In `ticket-card-signals`, "Sin técnico" is rendered twice when unassigned (once as the technician fallback and once as an exception badge), creating visual clutter.
4. The `.badge-exception` class is not formally defined in `App.css`, causing exception badges to lack consistent `inline-flex` alignment, gap, and 6px border-radius conforming to `DESIGN.md`.

## Solution
1. Standardize `.badge-exception` in `App.css` to adhere to `DESIGN.md` (display inline-flex, 6px radius, 12px font size, 500 font weight, vertical centering).
2. Enhance `AdminTicketCard.jsx`:
   - Add `.is-stale` / `.ticket-card-stale` modifier to `.ticket-card` when `isTicketStale` is true, providing a subtle border and signal cue.
   - Add descriptive tooltip to the "Vencido" badge: `title="Tiempo límite de atención superado (SLA vencido)"` and `data-testid="sla-stale-badge"`.
   - Remove the duplicate "Sin técnico" pill from `renderExceptionBadges`, letting the technician signal row handle the unassigned state cleanly.
3. Update and extend unit tests in `AdminTicketCard.test.jsx`.

## Capabilities
### New Capabilities
- `sla-indicators`: Consistent, accessible visual cues for tickets that exceed SLA thresholds in the admin card view.

## Impact
- **Modified Files:**
  - `frontend/src/App.css`
  - `frontend/src/features/admin/components/AdminTicketCard.jsx`
  - `frontend/src/tests/components/AdminTicketCard.test.jsx`
- **Dependencies:** None.
- **Breaking Changes:** None. Fully backwards-compatible.
