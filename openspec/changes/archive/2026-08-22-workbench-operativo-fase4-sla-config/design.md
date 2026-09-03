# Design: Multi-tenant SLA Configuration per Workshop (Fase 4)

## Technical Approach

Enable workshop-level custom SLA thresholds per active status (`EN_ESPERA_INGRESO`, `EN_REVISION`, `EN_REPARACION`) using a JSON column on the `shops` table. A centralized fallback resolver `get_effective_sla_thresholds()` merges tenant overrides with system defaults (`DEFAULT_SLA_THRESHOLDS_HOURS`). REST endpoints (`GET`/`PATCH /shops/sla-config`) enforce validation (`1 <= hours <= 720`), guarded by `admin_guard`. Dynamic query building in `ticket_service.py` prioritizes overdue tickets using tenant-specific time windows in SQL `case()` statements. The frontend fetches configuration via React Query, evaluates overdue badges in `date.js` (`isTicketStale`), and provides an admin configuration modal (`SlaSettingsModal.jsx`).

## Architecture Decisions

| Decision | Option Chosen | Alternatives Considered | Tradeoff & Rationale |
|---|---|---|---|
| **SLA Storage Model** | JSON column (`sla_config`) on `shops` | Dedicated `shop_sla_configs` table | JSON column provides schema flexibility for status additions without schema migrations while maintaining zero join overhead during shop loads. |
| **Fallback & Merging** | Pure helper merging defaults with overrides in application layer | Store full default duplicate row per tenant | Zero storage redundancy, auto-inherits new system statuses, and guarantees resilience if a tenant overrides only 1 status. |
| **SQL Sorting Evaluation** | Dynamic `timedelta` injection in `case()` statement during `list_tickets` | Raw SQL string formatting or triggers | Dynamic SQLAlchemy `case()` prevents SQL injection, uses index-friendly arithmetic against `func.coalesce(updated_at, created_at)`, and respects tenant thresholds. |
| **Frontend State Sync** | React Query caching with automatic cache invalidation on mutation | Local component state or global Redux store | Aligns with existing `@tanstack/react-query` pattern across `AdminDashboard.jsx`, ensuring immediate UI refresh on save/reset. |

## Data Flow

```
[Admin UI: SlaSettingsModal]
       │
       ▼ (PATCH /shops/sla-config)
[FastAPI Router: shops.py (admin_guard)]
       │
       ▼ (Pydantic validation: 1-720 hrs)
[Shop Service: update_shop_sla_config] ──→ [PostgreSQL: shops.sla_config]
       │
       ▼ (get_effective_sla_thresholds)
[Ticket Service: list_tickets] ──────────→ Dynamic SQL case() Overdue Sort
       │
       ▼ (Effective Thresholds via React Query)
[UI Cards: isTicketStale(updated_at, status, slaThresholds)] ──→ Badge "Vencido"
```

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/models/shop.py` | Modify | Add `sla_config = mapped_column(JSON, nullable=True, default=dict)` |
| `backend/alembic/versions/b3c4d5e6f7a8_add_sla_config_to_shops.py` | Create | Alembic migration script adding `sla_config` column |
| `backend/app/schemas/shop.py` | Modify | Add `SlaConfigUpdate`, `SlaConfigResponse` schemas |
| `backend/app/services/shop_service.py` | Modify | Add `DEFAULT_SLA_THRESHOLDS_HOURS`, `get_effective_sla_thresholds`, `get_shop_sla_config`, `update_shop_sla_config` |
| `backend/app/services/ticket_service.py` | Modify | Update `list_tickets` and `is_ticket_sla_breached` with dynamic threshold resolution |
| `backend/app/routers/shops.py` | Modify | Add `GET /shops/sla-config` and `PATCH /shops/sla-config` endpoints |
| `frontend/src/utils/date.js` | Modify | Update `isTicketStale()` to accept optional custom thresholds map |
| `frontend/src/features/admin/components/SlaSettingsModal.jsx` | Create | Admin modal with inputs, validation (1-720h), and reset to defaults |
| `frontend/src/features/admin/AdminDashboard.jsx` | Modify | Add SLA settings button `<Sliders size={16} />`, query hook, and pass thresholds to cards |
| `frontend/src/features/admin/components/AdminTicketCard.jsx` | Modify | Pass `slaThresholds` into `isTicketStale` call |
| `frontend/src/features/admin/components/KanbanTicketCard.jsx` | Modify | Pass `slaThresholds` into `isTicketStale` call |
| `backend/tests/test_sla_config.py` | Create | Integration tests for GET/PATCH SLA config, validation, multi-tenant isolation |
| `frontend/src/tests/utils/date.test.js` | Modify | Add unit tests for `isTicketStale` with custom threshold overrides |

## Interfaces / Contracts

### Backend Schemas & Constants (`shop.py` / `shop_service.py`)

```python
DEFAULT_SLA_THRESHOLDS_HOURS: dict[str, int] = {
    "EN_ESPERA_INGRESO": 48,
    "EN_REVISION": 24,
    "EN_REPARACION": 48,
}

class SlaConfigUpdate(BaseModel):
    custom_thresholds: dict[str, int] = Field(..., description="Map of status to hours (1-720)")

    @field_validator("custom_thresholds")
    @classmethod
    def validate_keys_and_values(cls, v: dict[str, int]) -> dict[str, int]:
        allowed = set(DEFAULT_SLA_THRESHOLDS_HOURS.keys())
        for k, val in v.items():
            if k not in allowed:
                raise ValueError(f"Estado '{k}' no es configurable para SLA.")
            if not isinstance(val, int) or val < 1 or val > 720:
                raise ValueError(f"Horas para '{k}' deben ser entero entre 1 y 720.")
        return v

class SlaConfigResponse(BaseModel):
    effective_thresholds: dict[str, int]
    custom_thresholds: dict[str, int]
    default_thresholds: dict[str, int]
```

### Endpoints

- `GET /shops/sla-config` (Auth: `admin_guard`) -> `200 OK` `SlaConfigResponse`
- `PATCH /shops/sla-config` (Auth: `admin_guard`, Body: `SlaConfigUpdate`) -> `200 OK` `SlaConfigResponse`

### Frontend Signature (`date.js`)

```javascript
export function isTicketStale(iso, status, customThresholds = null) {
  if (!iso || !status) return false;
  const threshold = customThresholds?.[status] ?? SLA_THRESHOLDS_HOURS[status];
  if (threshold === null || threshold === undefined) return false;
  const date = new Date(iso);
  if (isNaN(date.getTime())) return false;
  const diffHours = (Date.now() - date.getTime()) / (1000 * 60 * 60);
  return diffHours >= threshold;
}
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit (Backend) | `get_effective_sla_thresholds` merging logic; `is_ticket_sla_breached` with custom thresholds | Pytest with parameterized dictionaries and edge cases (empty, partial, unknown keys) |
| Unit (Frontend) | `isTicketStale` with `customThresholds` parameter | Vitest unit tests checking default fallback vs custom override behavior |
| Integration (API) | `GET`/`PATCH /shops/sla-config` endpoints, validation errors (`<1`, `>720`, invalid status), RBAC (`admin_guard`), multi-tenant isolation | Pytest with `AsyncClient`, verify Shop A overrides do not affect Shop B |
| Integration (UI) | `SlaSettingsModal` render, form submit, reset defaults, and error messaging | Vitest + React Testing Library component tests |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

1. Apply Alembic migration `b3c4d5e6f7a8_add_sla_config_to_shops.py` (`ALTER TABLE shops ADD COLUMN sla_config JSON DEFAULT '{}'`).
2. Deploy backend service (reads existing empty/null as fallback defaults).
3. Deploy frontend bundle (fetches SLA config and activates modal).
4. No data backfill required.

## Open Questions

- None. Requirements, fallback matrix, and boundaries are fully defined.
