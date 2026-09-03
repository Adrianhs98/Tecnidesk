# Tasks: Multi-tenant SLA Configuration per Workshop (Fase 4)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 280-350 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | exception-ok |
| Chain strategy | size-exception |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend SLA model, schemas, service fallback engine, and REST endpoints | PR 1 | `pytest backend/tests/unit/test_sla_config.py backend/tests/integration/test_sla_config.py` | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/shops/sla-config` | `backend/app/models/shop.py`, `backend/alembic/versions/*`, `backend/app/routers/shops.py`, `backend/app/services/shop_service.py` |
| 2 | Dynamic SQL ticket ordering, frontend date helpers, and SLA settings modal | PR 1 | `npm test frontend/src/tests/utils/date.test.js frontend/src/tests/features/admin/SlaSettingsModal.test.jsx` | Open AdminDashboard -> Click SLA Settings -> Update hours -> Verify workbench card badge | `backend/app/services/ticket_service.py`, `frontend/src/api/shop.js`, `frontend/src/features/admin/components/SlaSettingsModal.jsx`, `frontend/src/features/admin/AdminDashboard.jsx` |

## Phase 1: Database Migration & Model Updates

- [x] 1.1 Add `sla_config = mapped_column(JSON, nullable=True, default=dict)` to `Shop` in `backend/app/models/shop.py`.
- [x] 1.2 Create Alembic migration `backend/alembic/versions/b3c4d5e6f7a8_add_sla_config_to_shops.py` adding `sla_config` column to `shops`.

## Phase 2: Backend Schemas, Service Helpers & REST Endpoints

- [x] 2.1 Add `SlaConfigUpdate` and `SlaConfigResponse` schemas with validation (1-720h) in `backend/app/schemas/shop.py`.
- [x] 2.2 Implement `DEFAULT_SLA_THRESHOLDS_HOURS`, `get_effective_sla_thresholds()`, `get_shop_sla_config()`, and `update_shop_sla_config()` in `backend/app/services/shop_service.py`.
- [x] 2.3 Implement `GET /shops/sla-config` and `PATCH /shops/sla-config` endpoints guarded by `admin_guard` in `backend/app/routers/shops.py`.

## Phase 3: Ticket Service & Dynamic Ordering Integration

- [x] 3.1 Update `is_ticket_sla_breached()` in `backend/app/services/ticket_service.py` to support dynamic custom thresholds.
- [x] 3.2 Update `list_tickets()` dynamic SQL `case()` statement in `backend/app/services/ticket_service.py` using tenant-effective SLA thresholds.

## Phase 4: Frontend Integration & Settings UI

- [x] 4.1 Update `isTicketStale()` in `frontend/src/utils/date.js` to accept optional `customThresholds` parameter.
- [x] 4.2 Create `frontend/src/api/shop.js` with `fetchSlaConfig` and `updateSlaConfig` API functions using `authFetch`.
- [x] 4.3 Create `frontend/src/features/admin/components/SlaSettingsModal.jsx` with input controls (1-720h), validation, and "Reset to Defaults".
- [x] 4.4 Update `frontend/src/features/admin/AdminDashboard.jsx` to fetch shop SLA config via React Query, render modal trigger button, and pass thresholds to card components.
- [x] 4.5 Update `AdminTicketCard.jsx` and `KanbanTicketCard.jsx` to forward `slaThresholds` to `isTicketStale()`.

## Phase 5: Automated Testing & Verification

- [x] 5.1 Create unit tests in `backend/tests/unit/test_sla_config.py` for threshold merging and boundary validation.
- [x] 5.2 Create integration tests in `backend/tests/integration/test_sla_config.py` for `GET`/`PATCH /shops/sla-config`, multi-tenant isolation, and RBAC guards.
- [x] 5.3 Update `frontend/src/tests/utils/date.test.js` to test `isTicketStale` with custom workshop overrides.
- [x] 5.4 Create component tests in `frontend/src/tests/features/admin/SlaSettingsModal.test.jsx` for modal render, validation, and mutation flows.
