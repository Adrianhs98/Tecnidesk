# Proposal: Workbench Operativo (Fase 5: Lead Time, Cycle Time & Bottleneck Analytics)

## Intent

Workshop owners, technicians, and evaluators lack visibility into operational turnaround times, stage bottlenecks, and SLA compliance. This change introduces an operational analytics engine computed over `ticket_status_history` and `shops.sla_config`, exposed via REST API and visualized in an administrative dashboard modal with zero third-party chart dependencies.

## Scope

### In Scope
- **Analytics Service Engine**: `get_workshop_cycle_time_metrics(db, shop_id, days=30)` computing Average Lead Time (intake to completion), Active Cycle Time (`EN_REPARACION`), per-status duration breakdown, primary bottleneck identification, SLA compliance rate, and completed vs in-progress counts.
- **REST API Endpoint**: `GET /tickets/analytics/cycle-times` protected by `subscription_guard` returning validated `CycleTimeAnalyticsResponse`.
- **Dashboard Modal UI**: `CycleTimeAnalyticsModal.jsx` accessible via "Métricas y Tiempos" (`<BarChart3 size={16} />`) in `AdminDashboard.jsx` featuring KPI summary cards and CSS stage duration bars with bottleneck badges.
- **Automated Tests**: Unit, integration, and UI tests covering calculations, multi-tenant isolation, and zero-data edge cases.

### Out of Scope
- Automated PDF/CSV export generation (deferred to future reporting phase).
- Third-party chart rendering libraries (using native CSS/HTML progress bars to avoid bundle bloat).

## Capabilities

### New Capabilities
- `cycle-time-analytics`: Operational Lead Time, Cycle Time, bottleneck analysis, and SLA compliance calculation engine with REST endpoint and dashboard visualization modal.

### Modified Capabilities
- None

## Approach

1. **Backend Engine**: Aggregate `Ticket` and `TicketStatusHistory` for the tenant within the past `days` (default 30). Compute lead time from creation to terminal states, active repair duration in `EN_REPARACION`, average time in each status, identify the slowest stage (bottleneck), and measure SLA breach rates against tenant thresholds (`sla_config`).
2. **REST API & Schemas**: Add `CycleTimeAnalyticsResponse` and `StatusDurationMetric` schemas in `schemas/ticket.py` and register `GET /tickets/analytics/cycle-times` in `routers/tickets.py`.
3. **Frontend Modal**: Implement `CycleTimeAnalyticsModal.jsx` with KPI cards, stage breakdown progress bars, and bottleneck indicator, integrated into `AdminDashboard.jsx`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/schemas/ticket.py` | Modified | Add Pydantic schemas for analytics response |
| `backend/app/services/ticket_service.py` | Modified | Implement `get_workshop_cycle_time_metrics` |
| `backend/app/routers/tickets.py` | Modified | Add `GET /tickets/analytics/cycle-times` endpoint |
| `frontend/src/features/admin/AdminDashboard.jsx` | Modified | Add "Métricas y Tiempos" action button and modal state |
| `frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx` | New | Analytics modal with KPI cards and bottleneck progress bars |
| `backend/tests/` & `frontend/src/tests/` | New/Modified | Test analytics calculations, isolation, and UI rendering |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Division by zero with 0 tickets in date window | Low | Default all averages to 0.0 with empty list fallback |
| Incomplete status history for legacy tickets | Low | Fallback to ticket `created_at` and `updated_at` timestamps |
| Multi-tenant data leakage in aggregation queries | Low | Strict `shop_id` filter on all joins and subqueries |

## Rollback Plan

Revert backend router/service changes and frontend modal additions. No database schema migrations are introduced, allowing instantaneous rollback without data loss.

## Dependencies

- `ticket_status_history` table (Phase 2).
- `shops.sla_config` tenant settings (Phase 4).

## Success Criteria

- [ ] `GET /tickets/analytics/cycle-times` returns accurate lead time, cycle time, bottleneck, and SLA compliance metrics.
- [ ] Tenant data isolation is strictly enforced across queries.
- [ ] Admin dashboard provides a responsive "Métricas y Tiempos" modal with zero bundle bloat.
- [ ] Handles zero-ticket and missing-history edge cases gracefully without 500 errors.
- [ ] 100% test pass rate across backend pytest and frontend Vitest suites.
