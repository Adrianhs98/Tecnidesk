# Architectural Decision Records (ADRs) — TecniDesk

## ADR-001: Route-based Architecture for Workshop Operational Analytics & Feature Gating

- **Date:** 2026-09-11
- **Status:** Accepted
- **Context:**
  Workshop owners need operational metrics (Lead Time, active cycle times, bottleneck detection, and SLA compliance) to evaluate workshop throughput and performance. Initially, this functionality was built as an embedded modal (`CycleTimeAnalyticsModal`) inside `AdminDashboard.jsx`.
  As the product matures, this module represents executive decision-making intelligence rather than high-frequency operational ticket handling. Furthermore, monetization strategy requires the flexibility to introduce feature-gating (e.g. Pro tier, paid analytics add-on, or trial limits) without destabilizing core dispatch operations.

- **Decision:**
  Extract operational analytics out of `AdminDashboard` and provide a dedicated first-class route (`/admin/metricas` mapped to `AdminAnalyticsPage`).

- **Rationale & Tradeoffs:**
  1. **Separation of Concerns:** High-frequency ticket intake and status transitions (the operational workbench) are completely decoupled from executive reporting and bottleneck diagnosis.
  2. **Feature Gating Readiness:** Future monetization requires restricting access based on shop subscription tier or add-on entitlements. A dedicated route enables declarative Route Guards (e.g., `<PlanGuard requiredFeature="cycle_analytics" />` or backend `Depends(require_plan_tier(...))`), paywall teasers, or upgrade redirects. In contrast, gating an embedded modal forces conditional button rendering, nesting modals within modals, and polluting the operational workbench with subscription logic.
  3. **Performance & Bundle Isolation:** Analytics uses its own query key, 2-minute stale time, and dedicated endpoint (`GET /tickets/analytics/cycle-times`). Separating it via `React.lazy` in the router prevents unnecessary re-renders in `AdminDashboard`.
  4. **User Experience:** Provides full desktop canvas for stage duration bars and metrics grids, preserves deep-linking/bookmarking for workshop owners, and enables direct navigation without loading the full workbench first.

- **Implementation:**
  - Route: `/admin/metricas` in `frontend/src/App.jsx` protected by `ProtectedRoute`.
  - Core Page: `frontend/src/pages/AdminAnalyticsPage.jsx`.
  - Feature View: `frontend/src/features/analytics/CycleTimeAnalyticsView.jsx`.
  - Backend Endpoint (already dedicated): `GET /tickets/analytics/cycle-times` in `backend/app/routers/tickets.py`.

## ADR-002: Executive Business Insights Engine & Confirmed Repair Rate Metrics

- **Date:** 2026-09-11
- **Status:** Accepted
- **Context:**
  Workshop owners need strategic KPIs previously isolated in external BI tools (Metabase): intake volume by brand/model, confirmed repair conversion rate, high-rotation parts with stock alerts, customer recurrence, technician throughput, and gross margin structure (labor vs parts).
  
- **Decision:**
  Implement a dedicated endpoint `GET /tickets/analytics/business-insights` protected by `admin_guard`, consumed alongside cycle times in a 2-subtab interface (`/admin/metricas`) using parallel TanStack queries with 2-minute stale time.
  
- **Key Domain Rules:**
  1. **Repair Rate Denominator Rule:** Confirmed repairs (`EN_REPARACION`, `ESPERANDO_REPUESTO`, `LISTO_PARA_RETIRAR`) are divided by valid intakes excluding rejected tickets (`status != 'NO_APROBADO'`). This ensures unrepairable or customer-declined quotes do not artificially distort brand repair feasibility.
  2. **Financial Margin Isolation:** Rejection tickets (`NO_APROBADO`) are strictly excluded from parts consumption and revenue aggregation.
  3. **Multi-Tenant Boundaries:** All aggregations filter strictly on `shop_id` with `admin_guard` privilege validation.
