# Proposal: Unify StatusBadge in Technician Portal

## Problem
Following the introduction of the standardized `<StatusBadge />` component in `src/components/shared/StatusBadge.jsx`, `TechnicianTicketCard.jsx` continues to render an outdated `.tech-status-pill` element with a `border-radius: 999px`, no background fill, and uncalibrated border colors.

This creates visual fragmentation between the Admin Workbench and the Technician Workbench, violating the design consistency principles established in `DESIGN.md`.

## Solution
1. Replace `.tech-status-pill` in `frontend/src/features/technician/TechnicianTicketCard.jsx` with the unified `<StatusBadge status={ticket.status} />`.
2. Remove redundant inline color resolution (`statusCfg`) from `TechnicianTicketCard.jsx`.
3. Add a dedicated test assertion in `TechnicianPortal.test.jsx` verifying that `TechnicianTicketCard` renders the unified status badge.

## Capabilities
### Modified Capabilities
- `status-badge`: Extend usage to the Technician Portal (`TechnicianTicketCard`) ensuring consistent badge styling across all dashboard interfaces.

## Impact
- **Modified Files:**
  - `frontend/src/features/technician/TechnicianTicketCard.jsx`
  - `frontend/src/tests/features/TechnicianPortal.test.jsx`
- **Dependencies:** Uses existing `<StatusBadge />` from `src/components/shared/StatusBadge.jsx`.
- **Breaking Changes:** None. Fully compatible with existing ticket data.
