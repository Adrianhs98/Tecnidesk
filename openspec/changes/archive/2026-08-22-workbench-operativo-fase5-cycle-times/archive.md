# SDD Archive: Workbench Operativo (Fase 5: Lead Time, Cycle Time & Bottleneck Analytics)

**Date Archived**: 2026-08-22  
**Change Name**: `2026-08-22-workbench-operativo-fase5-cycle-times`  
**Status**: `archived`  
**Artifact Store Mode**: `openspec`

## 1. Archival Manifest & Artifacts

- **[proposal.md](proposal.md)**: Proposal for operational analytics engine computing turnaround times, stage bottlenecks, and SLA compliance over `ticket_status_history` and `shops.sla_config`, exposed via REST API and visualized in an administrative dashboard modal.
- **[design.md](design.md)**: Architectural design covering in-memory Python aggregation layer, route declaration ordering to prevent path-parameter shadowing, zero-dependency pure CSS flexbox progress meters, Pydantic schemas, and threat matrix.
- **[tasks.md](tasks.md)**: All 14/14 implementation tasks completed and checked across 5 phases.

## 2. Implemented Capabilities & Highlights

1. **Schemas & Pydantic Contracts**:
   - Defined `StageDurationMetric` schema (`status`, `label`, `avg_hours`, `percentage_of_total`, `is_bottleneck`) in [backend/app/schemas/ticket.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/schemas/ticket.py).
   - Defined `CycleTimeAnalyticsResponse` schema (`lead_time_avg_hours`, `cycle_time_avg_hours`, `sla_compliance_rate`, `bottleneck_stage`, `stage_durations`, `completed_tickets_count`, `active_tickets_count`, etc.) in [backend/app/schemas/ticket.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/schemas/ticket.py).

2. **Analytics Engine Service**:
   - Implemented `get_workshop_cycle_time_metrics(db, shop_id, days=30)` in [backend/app/services/ticket_service.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/services/ticket_service.py).
   - Aggregates `Ticket`, `TicketStatusHistory`, and `Shop.sla_config` with strict multi-tenant isolation (`shop_id`).
   - Calculates Average Lead Time (intake to completion), Active Cycle Time (`EN_REPARACION`), per-stage duration breakdown, primary bottleneck identification, SLA compliance rate against tenant-configured thresholds, and zero-ticket edge case handling.

3. **REST API Endpoint Routing**:
   - Added `GET /tickets/analytics/cycle-times` in [backend/app/routers/tickets.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/app/routers/tickets.py).
   - Positioned endpoint before `/{ticket_id}` to prevent FastAPI route shadowing / UUID validation errors.
   - Enforced tenant authentication and `subscription_guard` protection.

4. **Frontend Client & Analytics Modal UI**:
   - Created `fetchCycleTimeAnalytics(days)` HTTP client helper using `authFetch` in [frontend/src/api/ticketAnalytics.js](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/api/ticketAnalytics.js).
   - Created [frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx) with period selector (7, 30, 90 days), KPI summary cards (Lead Time, Cycle Time, SLA Rate, Analyzed Tickets), bottleneck badge, and pure CSS stage progress bars.
   - Added styling in [frontend/src/App.css](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/App.css) for modal layout, KPI cards, and stage duration meters.
   - Integrated `<BarChart3 size={16} /> Métricas y Tiempos` trigger button and modal state into [frontend/src/features/admin/AdminDashboard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/AdminDashboard.jsx).

5. **Verification & Test Coverage**:
   - Backend unit tests ([backend/tests/unit/test_cycle_time_analytics.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/tests/unit/test_cycle_time_analytics.py)) covering duration math, zero-data fallbacks, bottleneck detection, and SLA compliance calculations.
   - Backend integration tests ([backend/tests/integration/test_cycle_time_api.py](file:///Users/adrianjosesoriano/Documents/Tecnidesk/backend/tests/integration/test_cycle_time_api.py)) covering route shadowing prevention, multi-tenant isolation, and subscription guard enforcement (121 pytest tests passing).
   - Frontend component tests ([frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/tests/components/CycleTimeAnalyticsModal.test.jsx)) covering modal rendering, period filtering, and empty states (74 Vitest tests passing).

## 3. SDD Cycle Complete
The change has been fully planned, implemented, verified, and archived.
Ready for next operations.
