# Proposal: Workbench Operativo (Fase 4: SLAs Multi-tenant Configurables por Taller)

## Intent

Different repair workshops operate under contrasting business models (e.g., express screen replacement vs. micro-soldering board repairs) requiring distinct SLA timelines. Hardcoded system SLA thresholds cause false overdue warnings or inadequate urgency. This change enables per-tenant configurable SLA thresholds per status backed by PostgreSQL JSONB, dynamic query/frontend evaluation, and an admin configuration UI.

## Scope

### In Scope
- **Tenant SLA Storage**: Add `sla_config` (JSONB) to `shops` table with fallback to system defaults (`EN_REVISION: 24`, `EN_ESPERA_INGRESO: 48`, `EN_REPARACION: 48`).
- **REST Endpoints**: `GET /shops/sla-config` and `PATCH /shops/sla-config` with Pydantic validation (positive integer hours) and subscription guard.
- **Dynamic SLA Engine**: Update backend `ticket_service.py` sorting/filtering and frontend `date.js` evaluation to use tenant-specific thresholds.
- **Admin Settings UI**: Add `SlaSettingsModal` in `AdminDashboard` with per-status numeric inputs, instant validation, and "Reset to Defaults" action.
- **Automated Tests**: Unit and integration tests covering multi-tenant isolation, threshold validation, and SLA breach calculations.

### Out of Scope
- Automated email/SMS escalation alerts upon SLA breach.
- Business hours/working days calendar masking (SLAs remain continuous elapsed hours).

## Capabilities

### New Capabilities
- `shop-sla-configuration`: Workshop-level customizable SLA thresholds per status with JSONB persistence, validation API, dynamic workbench sorting, and Admin settings modal.

### Modified Capabilities
- None

## Approach

1. **Database**: Add nullable JSONB column `sla_config` to `shops` with Alembic migration. Missing keys merge with default `SLA_THRESHOLDS_HOURS`.
2. **Backend API & Service**: Implement `GET`/`PATCH /shops/sla-config` in `shops.py`. Pass tenant SLA config into `ticket_service.py` `list_tickets` for dynamic SQL sorting and `is_ticket_sla_breached`.
3. **Frontend UI**: Create `SlaSettingsModal.jsx`, integrate into `AdminDashboard.jsx` toolbar, and pass active shop thresholds to `isTicketStale()` in `date.js`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/shop.py` | Modified | Add `sla_config` JSONB column |
| `backend/alembic/versions/*` | New | Migration adding `sla_config` to `shops` |
| `backend/app/schemas/shop.py` | Modified | Add Pydantic schemas for SLA config GET/PATCH |
| `backend/app/routers/shops.py` | Modified | Add `GET /shops/sla-config` and `PATCH /shops/sla-config` endpoints |
| `backend/app/services/ticket_service.py` | Modified | Dynamic SLA evaluation & SQL sorting with tenant thresholds |
| `frontend/src/features/admin/AdminDashboard.jsx` | Modified | Add SLA settings trigger button and modal wiring |
| `frontend/src/features/admin/components/SlaSettingsModal.jsx` | New | Configuration modal with inputs and reset action |
| `frontend/src/utils/date.js` | Modified | Support dynamic threshold maps in `isTicketStale()` |
| `backend/tests/` & `frontend/src/tests/` | New/Modified | Test multi-tenant isolation, validation, and UI flows |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Incomplete tenant config breaks SLA checks | Low | Strict fallback merging with default `SLA_THRESHOLDS_HOURS` |
| Invalid negative or non-integer SLA hours | Low | Pydantic field validators (`gt=0, le=720`) on PATCH payload |
| Stale frontend thresholds after settings update | Low | React Query cache invalidation on successful SLA PATCH |

## Rollback Plan

Revert Alembic migration (dropping `sla_config` column) and redeploy previous service/frontend build. Fallback code safely uses hardcoded defaults if column is absent.

## Dependencies

- Phase 2 Dynamic SLA Engine (`ticket_service.py`, `date.js`).

## Success Criteria

- [ ] Administrators can view and update custom SLA hours per status via `AdminDashboard`.
- [ ] Backend persists tenant configuration in JSONB and enforces positive integer boundaries.
- [ ] Workbench card badges and SQL sorting immediately reflect the workshop's customized thresholds.
- [ ] Unconfigured statuses gracefully default to system constants without runtime exceptions.
- [ ] 100% test pass rate across backend pytest and frontend Vitest suites.
