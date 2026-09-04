# Proposal: Unified StatusBadge Component

## Problem
Following the adoption of `DESIGN.md`, ticket status badges (Recibido, En diagnóstico, Esperando repuesto, Reparado, Entregado) are rendered with duplicated inline styling, manual icon resolution, and inconsistent padding across multiple surfaces:
- `AdminTicketCard.jsx` computes inline background opacity and border styles directly.
- `TechnicianTicketCard.jsx` renders a separate `.tech-status-pill` with borders only.
- In-flight or unknown statuses lack a unified fallback mechanism.

This visual fragmentation violates the single source of truth principle established in `DESIGN.md` and makes future design or accessibility adjustments fragile.

## Solution
Extract and standardize a reusable `<StatusBadge />` component in `frontend/src/components/shared/StatusBadge.jsx` that:
1. Consumes `STATUS_CONFIG` tokens (`color`, `bg`, `border`, `label`, `icon`).
2. Adheres strictly to `DESIGN.md` (6px radius, font size 12px, 500 weight, 1px matching border).
3. Supports optional `size` variants (`sm` for tables/cards, `md` for detail headers) and togglable icons.
4. Provides a robust fallback for unrecognized or custom status strings.
5. Replaces the inline badge in `AdminTicketCard.jsx` with full unit test coverage.

## Capabilities
### New Capabilities
- `status-badge`: Centralized rendering of ticket status badges with Airtable-inspired tokens, icons, and accessible contrast.

## Impact
- **New Files:**
  - `frontend/src/components/shared/StatusBadge.jsx`
  - `frontend/src/tests/components/StatusBadge.test.jsx`
- **Modified Files:**
  - `frontend/src/features/admin/components/AdminTicketCard.jsx`
- **Dependencies:** None. Uses existing `lucide-react` icons and `STATUS_CONFIG`.
- **Breaking Changes:** None. Fully backward-compatible.
