# Tasks: Workbench Operativo (Fase 2) — Dynamic SLAs, Status Audit Log & Strict Assignment

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~260-320 lines |
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
| 1 | Database model, relationship & Alembic migration for `ticket_status_history` | Single PR | `pytest backend/tests/unit/test_ticket_guards.py -k test_model` | `alembic upgrade head && alembic downgrade -1` | `backend/alembic/versions/*_add_ticket_status_history.py`, `backend/app/models/ticket_status_history.py` |
| 2 | Service guard, history audit logging & dynamic SLA SQL ordering | Single PR | `pytest backend/tests/unit/test_ticket_guards.py` | `pytest backend/tests/integration/test_tickets.py` | `backend/app/services/ticket_service.py`, `backend/app/routers/tickets.py` |
| 3 | Pydantic schemas, frontend SLA helpers & UI stale evaluation | Single PR | `npm test -- src/utils/date.test.js` | N/A (Frontend date helper and card badge evaluation) | `backend/app/schemas/ticket.py`, `frontend/src/utils/date.js`, `frontend/src/features/admin/components/AdminTicketCard.jsx` |
| 4 | Combinatorial Pytest test suite for guards, sorting & transitions | Single PR | `pytest backend/tests/unit/test_ticket_guards.py backend/tests/integration/test_tickets.py` | Full Pytest suite run | `backend/tests/unit/test_ticket_guards.py` |

## Phase 1: Database Model & Alembic Migration

- [x] 1.1 Create `backend/app/models/ticket_status_history.py` defining `TicketStatusHistory` model with foreign keys and timestamp columns.
- [x] 1.2 Update `backend/app/models/ticket.py` and `backend/app/models/__init__.py` to configure `status_history` relationship and export `TicketStatusHistory`.
- [x] 1.3 Create Alembic migration `backend/alembic/versions/*_add_ticket_status_history.py` creating table, indices (`ticket_id`, `changed_at`), and initial backfill.

## Phase 2: Core Service Layer: Strict Technician Guard & History Logging

- [x] 2.1 Define `UnassignedTechnicianError` in `backend/app/services/ticket_service.py` and assert `ticket.technician_id` is present before transitioning to `EN_REPARACION`.
- [x] 2.2 Add `_record_status_history()` helper in `backend/app/services/ticket_service.py` to synchronously insert `TicketStatusHistory` on all status transitions.
- [x] 2.3 Update `backend/app/routers/tickets.py` to pass `current_user.id` to status transitions and map `UnassignedTechnicianError` to HTTP 400 Bad Request.

## Phase 3: Dynamic SLA Calculation & SQL Ordering Refactoring

- [x] 3.1 Define `SLA_THRESHOLDS_HOURS` mapping in `backend/app/services/ticket_service.py` for status-specific thresholds and pause states.
- [x] 3.2 Refactor SLA breach computation in `backend/app/services/ticket_service.py` to calculate elapsed hours per status using `updated_at`.
- [x] 3.3 Update SQL query ordering in `backend/app/services/ticket_service.py` to prioritize `technician_id IS NULL` > Dynamic SLA breached > `created_at DESC`.

## Phase 4: Schemas & Frontend SLA Helper Integration

- [x] 4.1 Add `TicketStatusHistoryResponse` and update `TicketDetailResponse` in `backend/app/schemas/ticket.py` to include `status_history`.
- [x] 4.2 Update `frontend/src/utils/date.js` with `SLA_THRESHOLDS_HOURS` and update `isTicketStale()` to evaluate elapsed duration per status and handle paused states.
- [x] 4.3 Update `frontend/src/features/admin/components/AdminTicketCard.jsx` to pass status `updated_at` to stale evaluation and handle 400 technician guard errors.

## Phase 5: Comprehensive Pytest Test Suite

- [x] 5.1 Create unit tests in `backend/tests/unit/test_ticket_guards.py` verifying `UnassignedTechnicianError` when `technician_id` is None vs allowed when assigned.
- [x] 5.2 Add unit tests in `backend/tests/unit/test_ticket_guards.py` verifying `TicketStatusHistory` records are created for all service transition paths.
- [x] 5.3 Add parameterized unit tests in `backend/tests/unit/test_ticket_guards.py` verifying combinatorial workbench ordering (`unassigned` > `stale` > `created_at`).
- [x] 5.4 Update integration tests in `backend/tests/integration/test_tickets.py` verifying HTTP 400 on unassigned `EN_REPARACION` transitions and `status_history` payload in `GET /tickets/{id}`.
