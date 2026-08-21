# Tasks: Workbench Operativo Mínimo (Fase 1)

- [x] 1. Date Utilities & Backend `filter_group` Support
  - [x] 1.1 Implement `formatRelativeAge(iso)` and `isTicketStale(iso, status)` in `frontend/src/utils/date.js`
  - [x] 1.2 Add unit tests for date utilities in `frontend/src/tests/utils/date.test.js`
  - [x] 1.3 Add `filter_group: str | None = Query(None)` parameter to `list_tickets` endpoint in `backend/app/routers/tickets.py`
  - [x] 1.4 Update `list_tickets` in `backend/app/services/ticket_service.py` to filter `status.not_in([LISTO_PARA_RETIRAR, NO_APROBADO])` when `filter_group == "activos"`
  - [x] 1.5 Add backend integration test for `GET /tickets?filter_group=activos` validating synchronization with `GET /tickets/stats`

- [x] 2. AdminTicketCard Declutter & Operational Signals
  - [x] 2.1 Remove on-mount N+1 evidence fetching (`useEffect` calling `GET /tickets/{id}/evidences`) from `frontend/src/features/admin/components/AdminTicketCard.jsx`
  - [x] 2.2 Redesign `AdminTicketCard.jsx` surface: render device brand/model, masked tracking token, client full name, relative age, and status badge
  - [x] 2.3 Implement exception badges in `AdminTicketCard.jsx` (`Sin técnico`, `Sin diagnóstico`, `Vencido`, `Listo p/ retiro`, `Esperando aprobación`)
  - [x] 2.4 Implement contextual Smart Action CTA in `AdminTicketCard.jsx` (Priorities: *Asignar* -> *Diagnosticar* -> *WhatsApp Retiro/Seguimiento* -> *Ver Detalle*)
  - [x] 2.5 Ensure the detail modal (`showDetail === true`) preserves all deep inspection tools (PII toggle, PIN, parts selector, diagnostic notes, lazy-loaded evidence gallery)
  - [x] 2.6 Add unit/component tests for `AdminTicketCard` in `frontend/src/tests/components/AdminTicketCard.test.jsx`

- [x] 3. AdminDashboard Interactive KPI Filters & Visual Styling
  - [x] 3.1 Update `frontend/src/features/admin/AdminDashboard.jsx` to introduce `kpiFilter` state (`null | 'activos' | 'listos' | 'espera'`) with toggle handling and pagination reset
  - [x] 3.2 Update React Query `dashboardData` key and query function in `AdminDashboard.jsx` to pass `filter_group` or `ticket_status` based on `kpiFilter`
  - [x] 3.3 Convert the 4 KPI stat blocks into interactive `<button>` elements with `is-active` state indicators
  - [x] 3.4 Add Hallmark-aligned CSS tokens in `frontend/src/index.css` for `.admin-stat-card.is-active`, `.badge-exception` variants, and `.btn-smart-action` variants
  - [x] 3.5 Add dashboard integration tests in `frontend/src/tests/features/AdminDashboard.test.jsx`

- [x] 4. Verification & Build Validation
  - [x] 4.1 Run backend test suite (`pytest`) and verify all tests pass
  - [x] 4.2 Run frontend test suite (`npm test`) and verify all tests pass
  - [x] 4.3 Run frontend build check (`npm run build`) to ensure clean compilation and type safety

## Fase 1.1: Ordenamiento Inteligente & Telemetría
- [x] 1. Actualizar `list_tickets` para ordenar por falta de técnico y antigüedad >72h.
- [x] 2. Generar `telemetry_baseline.md` con las métricas actuales previas al release.
