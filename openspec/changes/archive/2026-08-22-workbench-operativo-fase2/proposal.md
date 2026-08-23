# Proposal: Workbench Operativo (Fase 2) — Dynamic SLAs, Status Audit Log & Strict Assignment

## Intent

Phase 1 established a decluttered workbench and KPI filters, but workshop throughput remains constrained by static 72h SLA thresholds, unlogged status transitions, and unassigned tickets advancing into repair. Phase 2 transforms the workbench into an operational engine with dynamic per-status SLAs, an immutable transition audit trail (`ticket_status_history`), and strict assignment validation.

## Scope

### In Scope
- **Dynamic SLA Calculation**: Status-specific SLA thresholds (e.g. `EN_REVISION`: 24h, `EN_REPARACION`: 48h) computed from transition timestamps with pause states for client approvals.
- **Transition Audit Log (`ticket_status_history`)**: Dedicated PostgreSQL table tracking `(id, ticket_id, from_status, to_status, changed_by_user_id, changed_at, reason)`.
- **Strict Technician Assignment Guard**: Backend validation blocking status transitions to active repair (`EN_REPARACION`, etc.) if `technician_id` is null.
- **Combinatorial Ordering & Validation Tests**: Pytest suite testing smart ordering priority (`technician_id IS NULL` > `stale` > `created_at`) and state guards.

### Out of Scope
- Kanban column board view (deferred to Phase 3).
- Shop-configurable SLA settings UI in admin settings (deferred to Phase 4).

## Capabilities

### New Capabilities
- `dynamic-sla-calculation`: Dynamic SLA calculation based on status-specific thresholds and `ticket_status_history` timestamps instead of global 72h creation age.
- `ticket-status-history`: PostgreSQL audit table and backend service logging every ticket status transition with author, timestamp, and optional reason.
- `strict-technician-assignment`: State machine validation enforcing non-null `technician_id` prior to transitioning tickets into active repair stages.
- `combinatorial-order-tests`: Unit and integration test suite in pytest validating smart ticket ordering and guard edge cases.

### Modified Capabilities
None

## Approach

1. **Schema & History Migration**: Create Alembic migration for `ticket_status_history` table with indices on `ticket_id` and `changed_at`.
2. **Service Layer Guards & Logging**: Update `ticket_service.py` to assert `ticket.technician_id is not None` when transitioning to active repair, and record status history within the same database transaction.
3. **Dynamic SLA Engine**: Update SLA calculation to evaluate elapsed time against status-specific thresholds using the latest transition timestamp.
4. **Automated Test Matrix**: Implement parameterized pytest cases covering all status transitions, unassigned technician blocks, and workbench sorting orders.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/ticket_status_history.py` | New | SQLAlchemy model for transition audit history |
| `backend/alembic/versions/*_add_ticket_status_history.py` | New | Database migration for status history table |
| `backend/app/services/ticket_service.py` | Modified | Add assignment guard and status history logging |
| `backend/app/schemas/ticket.py` | Modified | Include status history and SLA metadata schemas |
| `frontend/src/utils/date.js` | Modified | Update SLA status calculations and relative timings |
| `backend/tests/unit/test_ticket_service.py` | New / Modified | Unit tests for guards, SLA calculations, and sorting |
| `backend/tests/integration/test_tickets.py` | Modified | Integration tests for status transitions and history |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Status changes failing due to unassigned legacy tickets | Med | Provide clear 400 Bad Request error detail; enforce guard only on forward repair transitions |
| N+1 queries when fetching status history for ticket lists | Low | Index `ticket_status_history.ticket_id`; join or query latest transition efficiently |

## Rollback Plan

1. Revert backend code changes in `ticket_service.py` and router schemas.
2. Run `alembic downgrade -1` to roll back the `ticket_status_history` migration.
3. Revert frontend SLA helper changes in `src/utils/date.js`.

## Dependencies

- None (builds on Phase 1 baseline workbench).

## Success Criteria

- [ ] Status transitions to `EN_REPARACION` fail with HTTP 400 if `technician_id` is null.
- [ ] Every status update creates an immutable record in `ticket_status_history`.
- [ ] Dynamic SLA alerts trigger according to per-status elapsed time rather than global ticket creation date.
- [ ] Automated test suite achieves 100% pass rate on status transition matrix and sorting order combinations.
