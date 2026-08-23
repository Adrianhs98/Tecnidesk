# SDD Archive: Workbench Operativo (Fase 2) — Dynamic SLAs, Status Audit Log & Strict Assignment

**Date Archived**: 2026-08-22  
**Change Name**: `2026-08-22-workbench-operativo-fase2`  
**Status**: `archived`  
**Artifact Store Mode**: `openspec`

## 1. Archival Manifest & Artifacts

- **[proposal.md](proposal.md)**: Proposal for Dynamic SLAs, immutable transition audit log (`ticket_status_history`), strict technician assignment guard, and smart combinatorial ordering.
- **[design.md](design.md)**: Architectural design covering database schema, migration, service-layer guards, dynamic SLA rules, frontend helpers, and test matrix.
- **[tasks.md](tasks.md)**: All 16/16 implementation tasks completed and checked across 5 phases.

## 2. Implemented Capabilities & Highlights

1. **`ticket_status_history` Audit Log**:
   - Dedicated PostgreSQL table and SQLAlchemy model tracking `(id, ticket_id, from_status, to_status, changed_by_user_id, changed_at, reason)`.
   - Alembic migration `e8964d4b1a20_add_ticket_status_history.py` with foreign keys and indexes on `ticket_id` and `changed_at`.
   - Synchronous audit recording on all service status transition points (`create_ticket`, `update_ticket_status`, `advance_ticket_stage`, `bulk_update_status`, `cancel_ticket`).

2. **Strict Technician Assignment Guard**:
   - `UnassignedTechnicianError` raised when attempting to transition tickets to `EN_REPARACION` without an assigned technician.
   - HTTP 400 Bad Request mapped in router with clear diagnostic error message.

3. **Dynamic SLA Engine & Smart Ordering**:
   - Status-specific SLA thresholds (`EN_REVISION`: 24h, `EN_REPARACION`: 48h, `EN_ESPERA_INGRESO`: 48h, `LISTO_PARA_RETIRAR`: 72h) with paused states (`ESPERANDO_APROBACION`, `ESPERANDO_REPUESTOS`, `NO_APROBADO`).
   - Dynamic SLA computation using `updated_at` (status timestamp).
   - SQL query ordering priority: `technician_id IS NULL` (unassigned) > Dynamic SLA breached > `created_at DESC`.

4. **Frontend & Schemas**:
   - Pydantic response schemas updated with `status_history` and `TicketStatusHistoryResponse`.
   - `frontend/src/utils/date.js` updated with dynamic `SLA_THRESHOLDS_HOURS` and paused state handling in `isTicketStale()`.
   - `AdminTicketCard.jsx` updated to evaluate status `updated_at` and handle 400 guard responses.

5. **Verification & Quality Gate**:
   - Backend test suite: 67 passed tests in pytest (including dedicated unit tests in `test_ticket_guards.py` and integration tests in `test_tickets.py`).
   - 0 regression or lint errors.

## 3. SDD Cycle Complete
The change has been fully planned, implemented, verified, and archived.
