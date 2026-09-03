# Technical Design: Workbench Operativo (Fase 5: Lead Time, Cycle Time & Bottleneck Analytics)

## Technical Approach

Implement an operational analytics calculation engine in `ticket_service.py` that processes ticket status lifecycle histories (`TicketStatusHistory`) and SLA configurations (`Shop.sla_config`) over a configurable time window (`days`, default 30). Expose metrics through `GET /tickets/analytics/cycle-times` protected by `subscription_guard`, and display them in a responsive `CycleTimeAnalyticsModal.jsx` within `AdminDashboard.jsx` using zero-dependency CSS flexbox meters and KPI cards.

## Architecture Decisions

| Decision | Option Selected | Tradeoffs Considered | Rationale |
|----------|-----------------|----------------------|-----------|
| **Analytics Processing Layer** | In-Memory Python Aggregation over eager-loaded `TicketStatusHistory` | SQL Window Functions (`LEAD`/`LAG`) in PostgreSQL vs Python aggregation | Ensures 100% dialect parity between SQLite test suite and PostgreSQL production while maintaining sub-50ms execution on tenant-scoped 30-90 day windows. |
| **Route Declaration Order** | Register `/analytics/cycle-times` explicitly BEFORE `/{ticket_id}` in `routers/tickets.py` | Standalone router prefix `/analytics` vs `/tickets/analytics/*` | Preserves RESTful grouping under `/tickets` while eliminating FastAPI path-parameter shadowing where `"analytics"` could be parsed as a UUID. |
| **Frontend Visualization** | Pure CSS Flexbox Percentage Bars with `STATUS_CONFIG` tokens | Chart.js / Recharts vs Native CSS meters | Adds zero runtime dependencies or bundle overhead, ensures immediate render performance, and seamlessly inherits dark/light theme tokens. |
| **SLA Compliance Metric** | Stage-transition level compliance rate against effective thresholds | Ticket-level binary SLA pass/fail vs transition-level | Provides granular visibility across distinct workflow stages (e.g. revision vs repair) and matches the `sla_config` architecture from Phase 4. |

## Data Flow

```
[ AdminDashboard ]
       │  (1) Opens modal / Selects period (7/30/90d)
       ▼
[ fetchCycleTimeAnalytics(days) ] ── authFetch ──► [ GET /tickets/analytics/cycle-times ]
                                                              │ (2) subscription_guard
                                                              ▼
                                                   [ get_workshop_cycle_time_metrics ]
                                                              │ (3) Filter shop_id + cutoff
                                                              ├── Query Shop.sla_config
                                                              └── Query Tickets + StatusHistory
                                                              │ (4) In-memory lifecycle analysis
                                                              ▼
                                                   [ CycleTimeAnalyticsResponse ]
                                                              │ (5) JSON response
                                                              ▼
                                              [ CycleTimeAnalyticsModal UI ]
                                              (KPIs, Bottleneck Badge, CSS Bars)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/schemas/ticket.py` | Modify | Define `StageDurationMetric` and `CycleTimeAnalyticsResponse` schemas |
| `backend/app/services/ticket_service.py` | Modify | Implement `get_workshop_cycle_time_metrics(db, shop_id, days)` calculation logic |
| `backend/app/routers/tickets.py` | Modify | Add `GET /tickets/analytics/cycle-times` endpoint before `/{ticket_id}` |
| `frontend/src/api/ticketAnalytics.js` | Create | Export `fetchCycleTimeAnalytics(days)` HTTP client helper |
| `frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx` | Create | Modal with period selector, KPI summary cards, and CSS stage breakdown meters |
| `frontend/src/features/admin/AdminDashboard.jsx` | Modify | Add `<BarChart3 size={16} /> Métricas y Tiempos` trigger button and modal state |
| `backend/tests/unit/test_cycle_time_analytics.py` | Create | Unit tests for analytics calculations, edge cases (0 tickets, missing transitions) |
| `backend/tests/integration/test_cycle_time_api.py` | Create | Integration tests for endpoint auth, subscription guard, and multi-tenant isolation |
| `frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx` | Create | Component tests for modal rendering, period switching, and bottleneck display |

## Interfaces / Contracts

```python
# backend/app/schemas/ticket.py
class StageDurationMetric(BaseModel):
    status: TicketStatusEnum
    label: str
    avg_hours: float
    percentage_of_total: float
    is_bottleneck: bool

class CycleTimeAnalyticsResponse(BaseModel):
    lead_time_avg_hours: float
    cycle_time_avg_hours: float
    sla_compliance_rate: float
    bottleneck_stage: TicketStatusEnum | None = None
    bottleneck_stage_label: str | None = None
    tickets_analyzed_count: int
    completed_tickets_count: int
    active_tickets_count: int
    stage_durations: list[StageDurationMetric]
    time_window_days: int
```

```javascript
// frontend/src/api/ticketAnalytics.js
export const fetchCycleTimeAnalytics = async (days = 30) => {
  const response = await authFetch(`${API_BASE}/tickets/analytics/cycle-times?days=${days}`);
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || "Error al cargar métricas de ciclo");
  }
  return response.json();
};
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| **Unit (Backend)** | Duration math, bottleneck detection, SLA compliance rate calculation, zero-ticket fallbacks | `pytest` fixtures with synthetic `TicketStatusHistory` sequences (normal flow, revisions, delays) |
| **Integration (Backend)** | Multi-tenant isolation (`shop_id`), `subscription_guard` enforcement, route ordering (not matching `/{ticket_id}`) | `pytest-asyncio` + `httpx.AsyncClient` with multiple test shops and tokens |
| **Component (Frontend)** | Modal render, loading states, empty state ("Sin datos en el período"), period switching (7/30/90d), bottleneck highlight | `vitest` + `@testing-library/react` mocking `fetchCycleTimeAnalytics` |

## Threat Matrix

| Threat Category | Applicability | Expected Safe Behavior | Planned RED Test |
|-----------------|---------------|------------------------|------------------|
| **Route Shadowing / Collision** | Applicable | `/tickets/analytics/cycle-times` routed to analytics handler, not 422 UUID error on `/{ticket_id}` | Integration test asserting 200 OK for analytics endpoint |
| **Multi-Tenant Leakage** | Applicable | Query filters strictly on `Ticket.shop_id == current_user.shop_id`; Shop B cannot access Shop A data | Integration test comparing metrics between two isolated shops |
| **Subscription Bypass** | Applicable | Unsubscribed / expired shops receive 402 Payment Required via `subscription_guard` | Integration test requesting analytics with inactive subscription |
| **Shell / Subprocess Injection** | N/A | No shell commands or subprocess execution involved | N/A |
| **File / VCS Automation** | N/A | No filesystem or git automation boundaries involved | N/A |

## Migration / Rollout

No database schema migrations are required. The analytics engine queries existing `tickets`, `ticket_status_history`, and `shops.sla_config` tables. Deploy backend service and frontend modal simultaneously.

## Open Questions

None. Architecture and requirements are fully determined.
