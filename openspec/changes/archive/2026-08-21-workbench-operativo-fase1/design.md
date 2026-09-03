# Design: Workbench Operativo Mínimo (Fase 1)

**Status**: draft  
**Date**: 2026-08-21  
**Author**: SDD Architect  
**Spec Reference**: [`specs/workbench/spec.md`](specs/workbench/spec.md)  
**Proposal Reference**: [`proposal.md`](proposal.md)  

---

## 1. Architecture Overview

```
+---------------------------------------------------------------------------------------+
| FRONTEND (React 19 + Vite + Tailwind)                                                 |
|                                                                                       |
|  1. AdminDashboard.jsx                                                                |
|     - kpiFilter state: null | 'activos' | 'listos' | 'espera'                         |
|     - Interactive KPI Cards with active toggle indicator                              |
|     - React Query key: ['dashboardData', page, limit, searchQuery, dateFilter, kpi]   |
|                                                                                       |
|  2. AdminTicketCard.jsx (Workbench Layout)                                            |
|     - Surface Level: Device (Brand+Model), #Tracking, Client Name, Relative Age,       |
|       Status Badge, Technician Name / "Sin técnico", Exception Badges, Smart Action   |
|     - Eliminated: On-mount fetch to /evidences (N+1 query removed)                    |
|     - Lazy Modal Level: Client PII (phone/email), Device PIN, PartsSelector,          |
|       Diagnostic Notes, Evidences Gallery (fetched only on modal open)                |
|                                                                                       |
|  3. utils/date.js                                                                     |
|     - formatRelativeAge(iso): "Hoy", "Ayer", "Hace 3 días", "Hace 2 sem"              |
|     - isTicketStale(created_at, status): boolean (>72h in active state)               |
+-------------------------------------------+-------------------------------------------+
                                            | REST (JWT + subscription_guard)
                                            v
+---------------------------------------------------------------------------------------+
| BACKEND (FastAPI + SQLAlchemy 2.0 Async)                                              |
|                                                                                       |
|  GET /tickets?skip=0&limit=50&ticket_status=X&filter_group=activos&search=...         |
|  - If ticket_status is set: WHERE status = ticket_status                               |
|  - Else if filter_group == 'activos': WHERE status NOT IN (LISTO_PARA_RETIRAR, NO_APP)|
|  - Synchronized 1:1 with GET /tickets/stats aggregated query logic                    |
+---------------------------------------------------------------------------------------+
```

---

## 2. Component Design & Frontend State

### 2.1 `AdminDashboard.jsx` Refactor

#### State additions
```javascript
// State for KPI interactive filtering
const [kpiFilter, setKpiFilter] = useState(null); // null | 'activos' | 'listos' | 'espera'
```

#### Query Key and Fetch Logic
```javascript
const { data, isLoading: loading, isError, error: queryError, refetch: fetchData } = useQuery({
  queryKey: ['dashboardData', page, limit, searchQuery, dateFilter, kpiFilter],
  queryFn: async () => {
    const skip = page * limit;
    let url = `${API_BASE}/tickets?skip=${skip}&limit=${limit}`;
    
    if (searchQuery) {
      url += `&search=${encodeURIComponent(searchQuery.trim())}`;
    }
    if (dateFilter) {
      url += `&date_range=${encodeURIComponent(dateFilter)}`;
    }
    
    // Map KPI filter to backend parameters
    if (kpiFilter === 'listos') {
      url += `&ticket_status=LISTO_PARA_RETIRAR`;
    } else if (kpiFilter === 'espera') {
      url += `&ticket_status=EN_ESPERA_INGRESO`;
    } else if (kpiFilter === 'activos') {
      url += `&filter_group=activos`;
    }

    const ticketsRes = await authFetch(url);
    if (!ticketsRes.ok) throw new Error("Error al cargar tickets");
    const ticketsData = await ticketsRes.json();

    let statsData = { total: 0, activos: 0, listos: 0, espera: 0 };
    try {
      const statsRes = await authFetch(`${API_BASE}/tickets/stats`);
      if (statsRes.ok) statsData = await statsRes.json();
    } catch (err) {
      console.warn("Estadísticas no disponibles:", err);
    }

    return {
      tickets: ticketsData.items || [],
      totalItems: ticketsData.total || 0,
      stats: statsData,
    };
  }
});
```

#### Interactive KPI Handlers
```javascript
const handleKpiClick = (targetFilter) => {
  startTransition(() => {
    setKpiFilter(prev => (prev === targetFilter ? null : targetFilter));
    setPage(0); // Reset pagination on filter toggle
  });
};
```

#### KPI Cards Markup (Hallmark Anti-AI-Slop Styling)
```jsx
<div className="admin-stats-row">
  <button 
    type="button"
    className={`admin-stat-card ${kpiFilter === null ? 'is-active' : ''}`}
    onClick={() => handleKpiClick(null)}
  >
    <div className="admin-stat-label">Total equipos</div>
    <div className="admin-stat-value accent">{stats.total}</div>
  </button>

  <button 
    type="button"
    className={`admin-stat-card ${kpiFilter === 'activos' ? 'is-active' : ''}`}
    onClick={() => handleKpiClick('activos')}
  >
    <div className="admin-stat-label">En taller</div>
    <div className="admin-stat-value">{stats.activos}</div>
  </button>

  <button 
    type="button"
    className={`admin-stat-card ${kpiFilter === 'listos' ? 'is-active' : ''}`}
    onClick={() => handleKpiClick('listos')}
  >
    <div className="admin-stat-label">Listos</div>
    <div className="admin-stat-value success">{stats.listos}</div>
  </button>

  <button 
    type="button"
    className={`admin-stat-card ${kpiFilter === 'espera' ? 'is-active' : ''}`}
    onClick={() => handleKpiClick('espera')}
  >
    <div className="admin-stat-label">En espera</div>
    <div className="admin-stat-value warning">{stats.espera}</div>
  </button>
</div>
```

---

### 2.2 `AdminTicketCard.jsx` Declutter & Workbench Surface

#### Eliminated on Mount: N+1 Evidences Request
Lines 77–94 of current `AdminTicketCard.jsx` (which called `GET /tickets/{id}/evidences` for every card) are removed completely. Evidences are loaded via React Query inside the modal when `showDetail === true`.

#### Surface Data Hierarchy
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ iPhone 13 Pro                                                [EN REVISIÓN]  │
│ Apple  •  #TRK-8821  •  Cliente: Carlos Mendoza  •  🕒 Hace 3 días          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 👨‍🔧 Juan Técnico          ⚠️ [Sin Diagnóstico]  ⏰ [Vencido >72h]           │
├─────────────────────────────────────────────────────────────────────────────┤
│ [📝 Diagnosticar]   [💬 WhatsApp]     [⚙️ Estado ▼]            [Detalle →]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Exception Badges Helper
```javascript
const renderExceptionBadges = (ticket) => {
  const badges = [];
  
  if (!ticket.technician) {
    badges.push(
      <span key="no-tech" className="badge-exception badge-warning">
        <AlertTriangle size={12} /> Sin técnico
      </span>
    );
  }
  
  if (ticket.status === "EN_REVISION" && !ticket.diagnostic_notes) {
    badges.push(
      <span key="no-diag" className="badge-exception badge-muted">
        <Wrench size={12} /> Sin diagnóstico
      </span>
    );
  }
  
  if (isTicketStale(ticket.created_at, ticket.status)) {
    badges.push(
      <span key="stale" className="badge-exception badge-danger">
        <Clock size={12} /> Vencido
      </span>
    );
  }
  
  if (ticket.status === "LISTO_PARA_RETIRAR") {
    badges.push(
      <span key="ready" className="badge-exception badge-success">
        <PackageCheck size={12} /> Listo p/ retiro
      </span>
    );
  }
  
  if (ticket.status === "ESPERANDO_APROBACION") {
    badges.push(
      <span key="approval" className="badge-exception badge-amber">
        <Hourglass size={12} /> Esperando aprobación
      </span>
    );
  }

  return badges;
};
```

#### Smart Action Decision Logic
```javascript
const renderSmartAction = (ticket) => {
  // 1. Priority 1: No technician assigned -> Direct assign trigger
  if (!ticket.technician) {
    return (
      <button 
        className="btn-smart-action btn-smart-warning" 
        onClick={() => setShowDetail(true)}
      >
        <Wrench size={14} /> Asignar Técnico
      </button>
    );
  }

  // 2. Priority 2: In revision without diagnosis -> Direct diagnostic modal trigger
  if (ticket.status === "EN_REVISION" && !ticket.diagnostic_notes) {
    return (
      <button 
        className="btn-smart-action btn-smart-accent" 
        onClick={() => setShowDiagModal(true)}
      >
        <ClipboardList size={14} /> Diagnosticar
      </button>
    );
  }

  // 3. Priority 3: Ready for pickup -> WhatsApp notification
  if (ticket.status === "LISTO_PARA_RETIRAR" && waPhone) {
    return (
      <a
        href={`https://wa.me/${waPhone}?text=${encodeURIComponent(
          `Hola ${ticket.customer?.full_name || ""}, su equipo ${ticket.device_brand} ${ticket.device_model} (#${ticket.tracking_token}) está listo para ser retirado.`
        )}`}
        target="_blank"
        rel="noreferrer"
        className="btn-smart-action btn-smart-success"
      >
        <MessageCircle size={14} /> Notificar Retiro
      </a>
    );
  }

  // 4. Priority 4: Waiting approval -> WhatsApp quote follow-up
  if (ticket.status === "ESPERANDO_APROBACION" && waPhone) {
    return (
      <a
        href={`https://wa.me/${waPhone}?text=${encodeURIComponent(
          `Hola ${ticket.customer?.full_name || ""}, le recordamos que el presupuesto de su equipo ${ticket.device_brand} ${ticket.device_model} está disponible para su aprobación: ${window.location.origin}/tracking/${ticket.tracking_token}`
        )}`}
        target="_blank"
        rel="noreferrer"
        className="btn-smart-action btn-smart-amber"
      >
        <MessageCircle size={14} /> Seguir Presupuesto
      </a>
    );
  }

  // Default: Standard WhatsApp or detail button
  return (
    <button 
      className="btn-smart-action btn-smart-secondary" 
      onClick={() => setShowDetail(true)}
    >
      Ver Detalle →
    </button>
  );
};
```

---

## 3. Date Utilities (`src/utils/date.js`)

```javascript
/**
 * Retorna la antigüedad relativa en texto amigable para el escaneo de tickets.
 * @param {string|Date} iso - Timestamp ISO de creación
 * @returns {string} - "Hoy", "Ayer", "Hace 3 días", "Hace 2 sem", etc.
 */
export function formatRelativeAge(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  const now = new Date();
  
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return "Recién";
  if (diffHours < 24 && date.getDate() === now.getDate()) return "Hoy";
  if (diffDays === 1 || (diffHours < 48 && date.getDate() === now.getDate() - 1)) return "Ayer";
  if (diffDays < 7) return `Hace ${diffDays} días`;
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `Hace ${weeks} sem${weeks > 1 ? "s" : ""}`;
  }
  return formatOnlyDate(iso);
}

/**
 * Determina si un ticket se encuentra vencido/estancado (>72 horas en estado activo).
 * @param {string|Date} iso - Timestamp ISO de creación
 * @param {string} status - Estado actual del ticket
 * @returns {boolean}
 */
export function isTicketStale(iso, status) {
  if (!iso) return false;
  // Estados cerrados no se consideran vencidos
  if (["LISTO_PARA_RETIRAR", "NO_APROBADO", "ENTREGADO"].includes(status)) {
    return false;
  }
  const date = new Date(iso);
  const now = new Date();
  const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
  return diffHours >= 72; // 3 días de umbral operativo
}
```

---

## 4. Backend Adjustments

### 4.1 Router Update (`backend/app/routers/tickets.py`)

```python
@router.get(
    "",
    response_model=PaginatedResponse[TicketListResponse],
    summary="Listar Tickets",
    description="Obtiene los últimos tickets del taller, con filtrado opcional.",
)
async def list_tickets(
    ticket_status: TicketStatusEnum | None = Query(None, description="Filtra por estado exacto (ej. Recibido)"),
    filter_group: str | None = Query(None, description="Filtro agrupado ('activos')"),
    search: str | None = Query(None, description="Término de búsqueda general"),
    date_range: str | None = Query(None, description="Filtra por fecha, ej. 2026-01-01,2026-01-31"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima a retornar (cap: 200)"),
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    items, total = await ticket_service.list_tickets(
        db=db,
        shop_id=current_user.shop_id,
        skip=skip,
        limit=limit,
        status=ticket_status,
        filter_group=filter_group,
        search=search,
        date_range=date_range
    )
    return PaginatedResponse(items=items, total=total)
```

### 4.2 Service Update (`backend/app/services/ticket_service.py`)

```python
async def list_tickets(
    db: AsyncSession,
    shop_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: TicketStatusEnum | None = None,
    filter_group: str | None = None,
    search: str | None = None,
    date_range: str | None = None
) -> tuple[list[Ticket], int]:
    limit = min(limit, 200)

    stmt = (
        select(Ticket)
        .join(Customer, Ticket.customer_id == Customer.id)
        .where(Ticket.shop_id == shop_id)
        .options(
            selectinload(Ticket.customer),
            selectinload(Ticket.technician),
        )
    )

    # 1. Filtro exacto por estado tiene precedencia
    if status is not None:
        stmt = stmt.where(Ticket.status == status)
    # 2. Filtro agrupado ('activos') sincronizado con get_ticket_stats
    elif filter_group == "activos":
        estados_inactivos = [
            TicketStatusEnum.LISTO_PARA_RETIRAR,
            TicketStatusEnum.NO_APROBADO,
        ]
        stmt = stmt.where(Ticket.status.not_in(estados_inactivos))
    
    if search:
        search_term = f"%{search}%"
        conditions = [
            Customer.full_name.ilike(search_term),
            Ticket.device_brand.ilike(search_term),
            Ticket.device_model.ilike(search_term)
        ]
        try:
            parsed_id = uuid.UUID(search)
            conditions.append(Ticket.id == parsed_id)
        except ValueError:
            pass
            
        stmt = stmt.where(or_(*conditions))
            
    if date_range:
        parts = date_range.split(',')
        if len(parts) == 2:
            from datetime import datetime
            try:
                start_date = datetime.strptime(parts[0], '%Y-%m-%d')
                end_date = datetime.strptime(parts[1], '%Y-%m-%d')
                stmt = stmt.where(Ticket.created_at >= start_date, Ticket.created_at <= end_date)
            except ValueError:
                pass

    total_query = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one_or_none() or 0

    stmt = stmt.order_by(Ticket.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    tickets = list(result.scalars().all())

    for t in tickets:
        decrypted = decrypt_pin(t.pin_or_password)
        t.__dict__["device_password"] = decrypted if decrypted else None
        _clear_pin(t)

    return tickets, total
```

---

## 5. CSS & Visual Styles (Workbench Tokens)

Add styles to `frontend/src/index.css` (or `AdminDashboard.css` / Tailwind classes):

```css
/* KPI Interactive State */
.admin-stat-card {
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease, transform 0.1s ease;
  user-select: none;
  text-align: left;
  background: var(--surface);
  border: 1px solid var(--border);
}

.admin-stat-card:hover {
  border-color: var(--accent);
  background: var(--surface2);
}

.admin-stat-card:active {
  transform: scale(0.98);
}

.admin-stat-card.is-active {
  border-color: var(--accent);
  background: rgba(201, 167, 106, 0.08);
  box-shadow: 0 0 0 1px var(--accent);
}

/* Exception Badges */
.badge-exception {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.badge-warning {
  background: rgba(204, 143, 90, 0.12);
  color: var(--warning);
  border: 1px solid rgba(204, 143, 90, 0.3);
}

.badge-danger {
  background: rgba(157, 92, 82, 0.12);
  color: var(--danger);
  border: 1px solid rgba(157, 92, 82, 0.3);
}

.badge-muted {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text3);
  border: 1px solid var(--border);
}

.badge-success {
  background: rgba(78, 159, 125, 0.12);
  color: var(--success);
  border: 1px solid rgba(78, 159, 125, 0.3);
}

.badge-amber {
  background: rgba(201, 167, 106, 0.12);
  color: var(--accent);
  border: 1px solid rgba(201, 167, 106, 0.3);
}

/* Smart Action Buttons */
.btn-smart-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s ease;
}

.btn-smart-warning {
  background: var(--warning);
  color: #111;
  border: 1px solid var(--warning);
}

.btn-smart-accent {
  background: var(--accent);
  color: #111;
  border: 1px solid var(--accent);
}

.btn-smart-success {
  background: rgba(37, 211, 102, 0.15);
  color: var(--whatsapp);
  border: 1px solid rgba(37, 211, 102, 0.3);
}

.btn-smart-secondary {
  background: var(--surface2);
  color: var(--text1);
  border: 1px solid var(--border);
}
```
