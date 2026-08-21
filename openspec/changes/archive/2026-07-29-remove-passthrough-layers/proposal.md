# Proposal: Remove Passthrough Layers
## Intent
Eliminate passthrough service wrappers that add indirection with zero business value.
## Scope
### In Scope
- Inline `inventory_service.py` pure DB queries (`list_inventory`, `create_inventory_item`, `update_inventory_item`, `delete_inventory_item`, `restock_inventory_item`) into `routers/inventory.py`.
- Inline `ClientService.get_clients` into `routers/clients.py`.
- Delete `client_service.py`.
### Out of Scope
- `deduct_stock` and `restore_stock` in `inventory_service.py` (real business logic — KEEP).
- Frontend.
- Auth layer.
- ticket_service.
- technician_service.
## Capabilities
### New Capabilities
None
### Modified Capabilities
None
## Approach
Move SQLAlchemy queries directly into endpoints; remove class wrapper for ClientService; keep inventory_service.py only for `deduct_stock` and `restore_stock`.
## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| Backend Services | Refactor | `client_service.py` deleted, `inventory_service.py` slimmed down |
| Backend Routers | Refactor | `routers/clients.py` and `routers/inventory.py` include DB queries directly |
## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Merge conflicts | Low | Communicate with team, merge quickly |
| Missing an import | Low | Use IDE linting and test coverage |
## Rollback Plan
Revert commit via git; service files remain in git history.
## Dependencies
None
## Success Criteria
- [ ] `client_service.py` is removed.
- [ ] `routers/clients.py` calls DB directly for `get_clients`.
- [ ] `routers/inventory.py` calls DB directly for basic CRUD.
- [ ] `inventory_service.py` only retains `deduct_stock` and `restore_stock`.
