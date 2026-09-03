# Tasks: Workbench Operativo (Fase 5: Lead Time, Cycle Time & Bottleneck Analytics)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 350-420 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | exception-ok |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Analytics Engine & REST API | PR 1 | `pytest backend/tests/unit/test_cycle_time_analytics.py backend/tests/integration/test_cycle_time_api.py` | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/tickets/analytics/cycle-times` | `backend/app/schemas/ticket.py`, `backend/app/services/ticket_service.py`, `backend/app/routers/tickets.py` |
| 2 | Frontend Client & Analytics Modal UI | PR 1 | `npm --prefix frontend test frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx` | Open AdminDashboard -> Click "Métricas y Tiempos" | `frontend/src/api/ticketAnalytics.js`, `frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx`, `frontend/src/features/admin/AdminDashboard.jsx`, `frontend/src/App.css` |

## Phase 1: Schemas & Pydantic Contracts

- [x] 1.1 Add `StageDurationMetric` schema (`status`, `label`, `avg_hours`, `percentage_of_total`, `is_bottleneck`) in [backend/app/schemas/ticket.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/schemas/ticket.py).
- [x] 1.2 Add `CycleTimeAnalyticsResponse` schema with lead/cycle time, SLA rate, bottleneck stage, and counts in [backend/app/schemas/ticket.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/schemas/ticket.py).

## Phase 2: Analytics Engine Service

- [x] 2.1 [RED] Write unit tests in [backend/tests/unit/test_cycle_time_analytics.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/tests/unit/test_cycle_time_analytics.py) asserting zero-ticket fallbacks, duration math, and bottleneck detection.
- [x] 2.2 Implement `get_workshop_cycle_time_metrics` in [backend/app/services/ticket_service.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/services/ticket_service.py) querying `Ticket`, `TicketStatusHistory`, and `Shop.sla_config`.
- [x] 2.3 Add stage duration breakdown, active cycle time calculation, and SLA compliance rate logic in [backend/app/services/ticket_service.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/services/ticket_service.py).

## Phase 3: REST API Endpoint Routing

- [x] 3.1 [RED] Write threat-matrix integration tests in [backend/tests/integration/test_cycle_time_api.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/tests/integration/test_cycle_time_api.py) for Route Shadowing, Multi-Tenant Leakage, and Subscription Bypass.
- [x] 3.2 Add `GET /tickets/analytics/cycle-times` before `/{ticket_id}` with `subscription_guard` in [backend/app/routers/tickets.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/routers/tickets.py).

## Phase 4: Frontend Client & Analytics Modal UI

- [x] 4.1 Create HTTP client helper `fetchCycleTimeAnalytics(days)` in [frontend/src/api/ticketAnalytics.js](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/api/ticketAnalytics.js).
- [x] 4.2 Create `CycleTimeAnalyticsModal.jsx` with KPI cards and CSS bottleneck progress bars in [frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx).
- [x] 4.3 Add CSS styles for analytics modal, KPI metrics, and stage progress meters in [frontend/src/App.css](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/App.css).
- [x] 4.4 Integrate "Métricas y Tiempos" action button and modal state into [frontend/src/features/admin/AdminDashboard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/AdminDashboard.jsx).

## Phase 5: Verification & Testing

- [x] 5.1 Create component tests for modal rendering, period filtering, and empty states in [frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx).
- [x] 5.2 Execute backend test suite: `pytest backend/tests/unit/test_cycle_time_analytics.py backend/tests/integration/test_cycle_time_api.py`.
- [x] 5.3 Execute frontend test suite: `npm --prefix frontend test frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx`.
