Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Review Workload Forecast

| Metric | Estimate | Justification |
|---|---|---|
| Total lines modified | ~150-200 | Moving queries to endpoints, deleting wrapper methods and file. |
| Conceptual risk | Low | Only moving existing queries, no logic changes. |
| Blast radius | Low | Limited to inventory and client routers. |

## Suggested Work Units

| Unit | Complexity | Scope |
|---|---|---|
| Phase 1: Clients Refactor | Low | `routers/clients.py`, `backend/app/services/client_service.py` |
| Phase 2: Inventory Refactor | Low | `routers/inventory.py`, `backend/app/services/inventory_service.py` |
| Phase 3: Verification | Low | Verify syntax and run backend |

## Execution Plan

### Phase 1: Refactor `routers/clients.py` and delete `client_service.py`
- [x] 1.1 Inline `Customer` query directly into `routers/clients.py` using `select`, `or_`, `func.count()`, `ilike`.
- [x] 1.2 Remove `ClientService` import from `routers/clients.py`.
- [x] 1.3 Delete `backend/app/services/client_service.py`.

### Phase 2: Refactor `routers/inventory.py` and `inventory_service.py`
- [x] 2.1 Inline `list_inventory` query into `GET /inventory` in `routers/inventory.py`.
- [x] 2.2 Inline `create_inventory_item` logic into `POST /inventory` in `routers/inventory.py`.
- [x] 2.3 Inline `update_inventory_item` logic into `PATCH /inventory/{item_id}` in `routers/inventory.py`.
- [x] 2.4 Inline `restock_inventory_item` logic into `POST /inventory/{item_id}/restock` in `routers/inventory.py`.
- [x] 2.5 Inline `delete_inventory_item` logic into `DELETE /inventory/{item_id}` in `routers/inventory.py`.
- [x] 2.6 Remove `list_inventory`, `create_inventory_item`, `update_inventory_item`, `restock_inventory_item`, `delete_inventory_item` from `backend/app/services/inventory_service.py`, leaving only `deduct_stock` and `restore_stock`.

### Phase 3: Verification & Cleanup
- [x] 3.1 Verify syntax/imports with python compile or pytest.
- [x] 3.2 Verify backend runs cleanly without missing imports.

