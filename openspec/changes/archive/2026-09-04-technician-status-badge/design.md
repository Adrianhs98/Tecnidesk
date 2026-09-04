# Design: Technician Portal StatusBadge Unification

## Architecture Overview
The `<StatusBadge />` component created in `src/components/shared/StatusBadge.jsx` is imported directly into `frontend/src/features/technician/TechnicianTicketCard.jsx`.

The outdated markup:
```jsx
<span className="tech-status-pill" style={{ borderColor: statusCfg.color, color: statusCfg.color }}>
  {statusCfg.label}
</span>
```
is replaced with:
```jsx
<StatusBadge status={ticket.status} />
```

## Decisions & Tradeoffs

### Decision 1: Remove redundant local `statusCfg` state in `TechnicianTicketCard`
- **Rationale:** `TechnicianTicketCard.jsx` previously imported `STATUS_CONFIG` solely to lookup `label` and `color` for the pill. Removing this local lookup reduces component complexity and delegates 100% of status rendering to `<StatusBadge />`.

### Decision 2: Maintain flexbox layout in `tech-card-badges`
- **Rationale:** The `.tech-card-badges` container uses flex layout (`gap: 8px`). `<StatusBadge />` has `flexShrink: 0`, ensuring proper alignment next to the SLA badge (`.tech-sla-badge`) without layout shifts.

## File Changes
- `frontend/src/features/technician/TechnicianTicketCard.jsx` (Replace `.tech-status-pill` with `<StatusBadge />`)
- `frontend/src/tests/features/TechnicianPortal.test.jsx` (Add unit test assertions for status badge rendering)
