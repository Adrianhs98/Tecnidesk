# Design: Unified StatusBadge Component

## Architecture Overview
The `<StatusBadge />` component is placed in `frontend/src/components/shared/StatusBadge.jsx` as a presentational, atomic UI component following the Container-Presentational design pattern.

It takes a `status` string prop, queries `STATUS_CONFIG` from `src/utils/constants.js`, and renders an accessible `<span className="ticket-badge">` container formatted with the exact Airtable design system tokens from `DESIGN.md`.

## Interface Contract
```javascript
/**
 * @param {Object} props
 * @param {string} props.status - Ticket status key (e.g. 'EN_ESPERA_INGRESO', 'EN_REVISION')
 * @param {boolean} [props.showIcon=true] - Whether to show the leading icon indicator
 * @param {string} [props.className=""] - Additional class names
 * @param {Object} [props.style={}] - Optional style overrides
 */
```

## Decisions & Tradeoffs

### Decision 1: Lookup via `STATUS_CONFIG` with graceful fallback
- **Rationale:** `STATUS_CONFIG` in `src/utils/constants.js` is the single source of truth for labels, steps, and colors.
- **Alternative:** Hardcoding switch cases inside the component.
- **Tradeoff:** Centralized configuration means any new state added to `constants.js` is automatically supported across the application without modifying JSX.

### Decision 2: Hybrid Token Application (Classes + Inline CSS Custom Properties)
- **Rationale:** The `.ticket-badge` class in `App.css` governs core typography (12px, font-weight 500), border-radius (6px), and flexbox layout. Dynamic colors (`cfg.bg`, `cfg.color`, `cfg.border`) are bound via `style` properties so theme transitions and status overrides work without needing pre-compiled class safelists.
- **Alternative:** Pure Tailwind dynamic strings like `bg-[${cfg.bg}]`.
- **Tradeoff:** Tailwind purges arbitrary dynamic class interpolations at build time. Inline custom properties are 100% deterministic and performant.

### Decision 3: Shared component placement in `components/shared/`
- **Rationale:** While currently applied to `AdminTicketCard`, the badge will subsequently be reused in `TechnicianTicketCard`, `TicketDetailModal`, and the customer `TrackingPortal`. Placing it in `shared/` prevents circular dependencies between feature folders.

## Migration & Integration Strategy
1. Build `<StatusBadge />` with 100% unit test coverage.
2. In `AdminTicketCard.jsx`, replace lines 374–382 with `<StatusBadge status={ticket.status} />`.
3. Verify that all 101 existing tests continue passing without regression.
