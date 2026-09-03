# SDD Archive: Workbench Operativo (Fase 4: SLAs Multi-tenant Configurables por Taller)

**Date Archived**: 2026-08-22  
**Change Name**: `2026-08-22-workbench-operativo-fase4-sla-config`  
**Status**: `archived`  
**Artifact Store Mode**: `openspec`

## 1. Archival Manifest & Artifacts

- **[proposal.md](proposal.md)**: Proposal for multi-tenant configurable SLA thresholds per workshop backed by PostgreSQL JSONB, dynamic SQL sorting & frontend evaluation, and admin settings modal.
- **[design.md](design.md)**: Architectural design covering database schema, service fallback engine, REST endpoints, ticket ordering dynamic SQL, frontend API client, `SlaSettingsModal` component, and verification test matrix.
- **[tasks.md](tasks.md)**: All 16/16 implementation tasks completed and checked across 5 phases.

## 2. Implemented Capabilities & Highlights

1. **Database Schema & Migration**:
   - Added `sla_config = mapped_column(JSON, nullable=True, default=dict)` to `Shop` model in `backend/app/models/shop.py`.
   - Created Alembic migration `backend/alembic/versions/b3c4d5e6f7a8_add_sla_config_to_shops.py` adding `sla_config` JSON column with zero-downtime nullable semantics.

2. **Backend Schemas & Service Fallback Engine**:
   - Created `SlaConfigUpdate` and `SlaConfigResponse` Pydantic schemas in `backend/app/schemas/shop.py` enforcing positive integer bounds (1 to 720 hours).
   - Implemented `DEFAULT_SLA_THRESHOLDS_HOURS` (`EN_REVISION: 24`, `EN_ESPERA_INGRESO: 48`, `EN_REPARACION: 48`) with `get_effective_sla_thresholds()` dictionary merger in `backend/app/services/shop_service.py`.
   - Added `get_shop_sla_config()` and `update_shop_sla_config()` in `shop_service.py` to persist per-workshop threshold maps.

3. **REST Endpoints**:
   - `GET /shops/sla-config`: Returns effective SLA thresholds merging shop overrides with system defaults, guarded by `admin_guard`.
   - `PATCH /shops/sla-config`: Updates workshop SLA overrides, validates status keys and hour values, and returns updated effective thresholds.

4. **Dynamic SQL Ordering & SLA Breach Calculation**:
   - Updated `is_ticket_sla_breached()` in `backend/app/services/ticket_service.py` to accept dynamic custom threshold maps.
   - Updated `list_tickets()` dynamic SQL `case()` statement in `ticket_service.py` to order overdue tickets according to tenant-effective SLA thresholds.

5. **Frontend Date Helpers & API Client**:
   - Extended `isTicketStale()` in `frontend/src/utils/date.js` to accept optional `customThresholds` parameter.
   - Created `frontend/src/api/shop.js` with `fetchSlaConfig` and `updateSlaConfig` utilizing `authFetch`.

6. **Admin SLA Settings Modal & Workbench Card Integration**:
   - Created `SlaSettingsModal.jsx` with per-status numeric inputs, bounds validation, error handling, and a "Reset to Defaults" option.
   - Integrated SLA settings trigger button and modal into `AdminDashboard.jsx` toolbar with React Query caching and automatic invalidation.
   - Passed dynamic `slaThresholds` to `AdminTicketCard.jsx` and `KanbanTicketCard.jsx` for accurate SLA warning badge calculation across list and Kanban views.

7. **Verification & Test Coverage**:
   - Backend unit tests (`backend/tests/unit/test_sla_config.py`) and integration tests (`backend/tests/integration/test_sla_config.py`) covering multi-tenant isolation, RBAC guards, and boundary checks (115 pytest tests passing).
   - Frontend date utility tests (`frontend/src/tests/utils/date.test.js`) and component tests (`frontend/src/tests/features/admin/SlaSettingsModal.test.jsx`) covering modal render, validation, and mutation flows (62 Vitest tests passing).

## 3. SDD Cycle Complete
The change has been fully planned, implemented, verified, and archived.
Ready for next operations.
