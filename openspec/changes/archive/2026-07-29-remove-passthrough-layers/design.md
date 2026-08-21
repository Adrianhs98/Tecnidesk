# Design: Remove Passthrough Layers

## Technical Approach
Inline DB queries into `routers/clients.py` and `routers/inventory.py`. Remove `client_service.py`. Keep `deduct_stock` and `restore_stock` in `inventory_service.py`.

## Architecture Decisions
- **Decision 1**: Direct DB access in routers for simple CRUD vs. service abstraction. 
  - *Rationale*: Zero business logic in CRUD passthroughs; direct async SQLAlchemy in endpoints reduces file jumps and maintenance overhead.
- **Decision 2**: Keep `inventory_service.py` for atomic stock operations (`deduct_stock`, `restore_stock`).
  - *Rationale*: `deduct_stock` contains atomic UPDATE with WHERE check and stock conflict error handling; it is also called by ticket workflows.

## Data Flow
Router -> AsyncSession (SQLAlchemy) -> DB Model -> Pydantic Schema.

## File Changes
- `backend/app/services/client_service.py`: Delete
- `backend/app/services/inventory_service.py`: Modify (remove `list_inventory`, `create_inventory_item`, `update_inventory_item`, `delete_inventory_item`, `restock_inventory_item`)
- `backend/app/routers/clients.py`: Modify (inline `select(Customer)...` query directly)
- `backend/app/routers/inventory.py`: Modify (inline `select(Inventory)...`, `add()`, `commit()`, `refresh()` directly into endpoints)

## Interfaces / Contracts
No change to HTTP API contracts or Pydantic schemas.

## Testing Strategy
Verify existing endpoints work via HTTP/tests or script verification.

## Threat Matrix
N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration
No migration required.
