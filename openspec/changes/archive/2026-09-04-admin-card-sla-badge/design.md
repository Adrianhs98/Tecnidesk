# Design: SLA Overdue Signal and Exception Badge Refinement

## Architecture Overview
This change refines exception badges and SLA overdue feedback in `AdminTicketCard.jsx` and `App.css`:

1. **CSS Token Definition (`App.css`):**
   - Formalize `.badge-exception` to guarantee vertical centering, `inline-flex` layout, and consistent 6px border-radius matching `DESIGN.md`.
   - Add `.ticket-card.is-stale` styles that introduce a subtle danger border cue (`rgba(157, 92, 82, 0.4)`) without visual aggressiveness.

2. **Component Refactor (`AdminTicketCard.jsx`):**
   - Compute `stale = isTicketStale(ticket.updated_at || ticket.created_at, ticket.status, slaThresholds)` once at the top of the component.
   - Conditionally add `is-stale` to the outer `<div className="ticket-card ...">`.
   - Add `title="Tiempo límite de atención superado (SLA vencido)"` and `data-testid="sla-stale-badge"` to the "Vencido" badge.
   - Remove the duplicate "Sin técnico" pill from `renderExceptionBadges()`, and display an `AlertTriangle` icon in the main technician signal row when unassigned.

## Decisions & Tradeoffs

### Decision 1: Remove redundant "Sin técnico" from `renderExceptionBadges()`
- **Rationale:** The technician signal row already indicates "Sin técnico" with warning colors. Having a second badge immediately adjacent with the identical label was confusing and created visual noise.
- **Tradeoff:** Clean visual hierarchy with exactly 1 source of truth for technician assignment on the card surface.

### Decision 2: Subtle card border for `.ticket-card.is-stale`
- **Rationale:** High-saturation red backgrounds distract from readability. A gentle border-color adjustment (`rgba(157, 92, 82, 0.4)`) immediately distinguishes overdue tickets while preserving the clean Airtable look.

## File Changes
- `frontend/src/App.css` (Add `.badge-exception` and `.ticket-card.is-stale`)
- `frontend/src/features/admin/components/AdminTicketCard.jsx` (Apply `is-stale`, tooltip, and remove duplicate signal)
- `frontend/src/tests/components/AdminTicketCard.test.jsx` (Update and add assertions for stale container and de-duplicated signal)
