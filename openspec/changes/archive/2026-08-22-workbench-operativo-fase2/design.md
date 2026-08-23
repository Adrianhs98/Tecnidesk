# Design: Workbench Operativo (Fase 2) — Dynamic SLAs, Status Audit Log & Strict Assignment

## Technical Approach

Phase 2 transitions the workbench from static 72h thresholds into a state-aware operational engine. The technical strategy incorporates:
1. **Audit Logging**: Persisting immutable status transitions in `ticket_status_history` synchronously within the database transaction for every status modification.
2. **Strict Assignment Guard**: Enforcing non-null `technician_id` in `ticket_service.py` before permitting transitions to active repair (`EN_REPARACION`), rejecting unassigned transitions with HTTP 400.
3. **Dynamic SLA Engine**: Shifting SLA evaluation from global ticket creation age to per-status elapsed durations (`updated_at` / `changed_at`) with state-specific thresholds and pause states in SQL sorting and frontend UI.

```
[Ticket Status Change Request]
               │
               ▼
   [Strict Assignment Guard] ──(No Tech & To EN_REPARACION)──→ [HTTP 400 Bad Request]
               │
               ▼ (Valid)
   [Update Ticket Status]
               │
   [Insert TicketStatusHistory]  (Same DB Transaction)
               │
   [Commit & Dispatch Webhook]
```

## Architecture Decisions

### Decision: Transition Audit Persistence & Model

| Option | Tradeoff | Decision |
|--------|----------|----------|
| JSONB array column on `tickets` | Fast reads, but difficult to query, index, and report across workshop | **Dedicated `ticket_status_history` table** with indexed FKs for relational integrity, indexability, and clean audit logs |
| Asynchronous event listener | Non-blocking, but risk of data inconsistency on rollback | **Synchronous transaction write** ensuring atomic commit of status update and history entry |

### Decision: Dynamic SLA Computation & SQL Sorting

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Querying/joining full history table on `list_tickets` | Exact per-transition historical timestamp, but causes heavy joins and pagination overhead | **SQL `CASE` evaluation on `Ticket.status` + `Ticket.updated_at`** for O(1) query performance and indexed sort |
| Client-side sorting | Offloads DB, but breaks server-side pagination (`skip`/`limit`) | **Server-side database sort order**: Unassigned (`technician_id IS NULL`) > Dynamic SLA breached > `created_at DESC` |

## Data Flow

```
Admin / Public Action
        │
        ▼
 Router: /tickets/{id}/status ──→ ticket_service.update_ticket_status()
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
     Guard: technician_id?                                      DB Transaction:
  [None & EN_REPARACION] → 400                         1. Update tickets.status
                                                       2. Insert ticket_status_history
                                                       3. Commit
                                                                 │
                                                                 ▼
                                                        _dispatch_webhook()
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/models/ticket_status_history.py` | Create | SQLAlchemy model for `ticket_status_history` |
| `backend/app/models/ticket.py` | Modify | Add `status_history` relationship and `last_status_changed_at` helper |
| `backend/app/models/__init__.py` | Modify | Export `TicketStatusHistory` for Alembic discovery |
| `backend/alembic/versions/*_add_ticket_status_history.py` | Create | Migration script creating `ticket_status_history` table & indices |
| `backend/app/services/ticket_service.py` | Modify | Add assignment guard, history logging helper, and dynamic SLA sorting |
| `backend/app/routers/tickets.py` | Modify | Map domain exceptions to HTTP 400 and pass user context |
| `backend/app/schemas/ticket.py` | Modify | Add `TicketStatusHistoryResponse`, update `TicketResponse` and `TicketDetailResponse` |
| `frontend/src/utils/date.js` | Modify | Add `SLA_THRESHOLDS_HOURS` and update `isTicketStale()` |
| `frontend/src/features/admin/components/AdminTicketCard.jsx` | Modify | Pass dynamic status timestamp to stale checks and handle guard errors |
| `backend/tests/unit/test_ticket_guards.py` | Create | Unit tests for assignment guard, dynamic SLA sorting, and status history |
| `backend/tests/integration/test_tickets.py` | Modify | Integration tests for status transition audit and 400 guard responses |

## Interfaces / Contracts

### 1. Database Schema (`ticket_status_history`)

```sql
CREATE TABLE ticket_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    from_status VARCHAR(50) NULL,
    to_status VARCHAR(50) NOT NULL,
    changed_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reason TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_ticket_status_history_ticket_id ON ticket_status_history(ticket_id);
CREATE INDEX ix_ticket_status_history_changed_at ON ticket_status_history(changed_at);
```

### 2. SLA Configuration & Dynamic Calculation

```python
SLA_THRESHOLDS_HOURS = {
    TicketStatusEnum.EN_ESPERA_INGRESO: 48,
    TicketStatusEnum.EN_REVISION: 24,
    TicketStatusEnum.EN_REPARACION: 48,
    TicketStatusEnum.ESPERANDO_APROBACION: None,  # Paused
    TicketStatusEnum.ESPERANDO_REPUESTO: None,    # Paused
    TicketStatusEnum.LISTO_PARA_RETIRAR: None,   # Ready
    TicketStatusEnum.NO_APROBADO: None,          # Terminal
}
```

### 3. Pydantic Schemas

```python
class TicketStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    from_status: str | None
    to_status: str
    changed_by_user_id: uuid.UUID | None
    changed_at: datetime
    reason: str | None

    model_config = {"from_attributes": True}

class TicketDetailResponse(TicketResponse):
    customer: CustomerBasicInfo | None = None
    technician: TechnicianBasicInfo | None = None
    items: list[TicketItemResponse] = []
    evidences: list[TicketEvidenceResponse] = []
    status_history: list[TicketStatusHistoryResponse] = []
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Assignment guard blocking unassigned `EN_REPARACION` | Parameterized tests verifying `UnassignedTechnicianError` when `technician_id=None` vs success when assigned |
| Unit | Transition audit history generation | Verify `TicketStatusHistory` records written for all service transitions (`create`, `update_status`, `diagnostic`, `approve`, `reject`) |
| Unit | Combinatorial sorting order | Verify SQL ordering: `technician_id IS NULL` > `stale` (per status SLA) > `created_at DESC` |
| Integration | `PATCH /tickets/{id}/status` guard response | Assert HTTP 400 with detail "Debe asignar un técnico responsable antes de iniciar la reparación." |
| Integration | Status history in `GET /tickets/{id}` | Assert `status_history` list populated with timestamps and user author |
| Frontend | `isTicketStale()` SLA evaluation | Unit tests checking threshold evaluation for 24h (`EN_REVISION`), 48h (`EN_REPARACION`), and paused states |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

1. Apply Alembic migration `add_ticket_status_history` creating table and indices.
2. Backfill initial history rows for existing tickets:
   ```sql
   INSERT INTO ticket_status_history (id, ticket_id, from_status, to_status, changed_at, created_at)
   SELECT gen_random_uuid(), id, NULL, status, created_at, created_at FROM tickets;
   ```
3. Deploy backend service and schema updates.
4. Deploy frontend date utility and workbench card updates.

## Open Questions

None — all requirements and technical constraints are well-defined.
