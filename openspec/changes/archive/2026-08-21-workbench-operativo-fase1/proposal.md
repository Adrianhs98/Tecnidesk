# Proposal: Workbench Operativo Mínimo — Dashboard de Control con Filtros KPI y Señales de Excepción

**Status**: proposed  
**Date**: 2026-08-21  
**Author**: SDD Orchestrator  

---

## 1. Problem & Context

The TecniDesk admin dashboard ([`AdminDashboard.jsx`](file:///C:/Users/cntmi/Desktop/Tecnidesk/frontend/src/features/admin/AdminDashboard.jsx)) currently operates as a flat paginated list of ticket cards. While functionally complete, it fails to support rapid operational decision-making in a real workshop environment:

1. **Cognitive overload per card**: Each [`AdminTicketCard.jsx`](file:///C:/Users/cntmi/Desktop/Tecnidesk/frontend/src/features/admin/components/AdminTicketCard.jsx) (~565 lines) surfaces customer PII (phone, email), encrypted PIN badge, full issue description, evidence count, diagnostic notes preview, and absolute dates — all at the scan level. A technician or shop owner scanning 15 cards must mentally filter signal from noise on every single one.

2. **N+1 network saturation**: Every card mounts a `useEffect` that fires `GET /tickets/{id}/evidences` immediately, producing 15 concurrent requests per page load regardless of whether the user will ever open that card's detail. This is pure waste.

3. **Static KPIs with no interaction**: The 4 stat blocks (Total, En taller, Listos, En espera) sourced from `GET /tickets/stats` are display-only. The admin sees "18 en taller" but cannot click it to filter the list — they must mentally correlate the number with the cards below.

4. **No operational signals**: There is no visual distinction between a ticket received 1 hour ago and one stagnating for 10 days. No badge for "unassigned technician", "missing diagnosis", or "ready but not picked up". The dashboard treats all tickets as equal, forcing the admin to open each detail modal to identify blockers.

5. **No contextual next-action**: The footer of every card shows the same controls (WhatsApp, status select, save) regardless of the ticket's operational state. A ticket in `EN_REVISION` without diagnostic notes needs a "Diagnose" action, not a generic status dropdown.

---

## 2. Proposed Solution

### 2.1 Decluttered Ticket Card

Reduce `AdminTicketCard.jsx` from a data-heavy panel to an operational scan unit. The card surface shows only:

- **Device identity**: `device_brand` + `device_model` + masked `tracking_token`.
- **Client**: `customer.full_name` only.
- **Relative age**: Human-readable elapsed time ("Hace 2h", "Hace 3 días") calculated from `ticket.created_at`.
- **Status badge**: Colored badge with semantic label from `STATUS_CONFIG`.
- **Responsible**: Technician name or highlighted `Sin técnico` warning badge.
- **Exception badges**: Compact visual alerts for operational anomalies (see §2.3).
- **Smart action button**: One contextual CTA per ticket state (see §2.4).

All remaining data (email, phone, PIN, full description, evidence gallery, parts selector, diagnostic notes) stays in the existing detail modal — accessible via "Ver detalle" link.

### 2.2 KPI Blocks as Dynamic Filters

Transform the 4 stat blocks in `AdminDashboard.jsx` into clickable filter toggles:

| KPI Block | Filter behavior | Backend mapping |
|---|---|---|
| **Total equipos** | Show all tickets (clear filter) | `ticket_status=` (none) |
| **En taller** | Show only active tickets | `ticket_status` NOT IN `LISTO_PARA_RETIRAR`, `NO_APROBADO` — requires a new `filter_group=activos` param in `GET /tickets` |
| **Listos** | Show ready-for-pickup | `ticket_status=LISTO_PARA_RETIRAR` |
| **En espera** | Show awaiting intake | `ticket_status=EN_ESPERA_INGRESO` |

Clicking a KPI applies its filter, resets pagination to page 0, and visually highlights the active KPI with an accent border. Clicking the already-active KPI clears the filter (toggle behavior). The filter integrates into the existing `useQuery` key alongside `searchQuery` and `dateFilter`.

### 2.3 Exception Badges

Compact inline badges rendered conditionally on each card:

| Badge | Condition | Visual |
|---|---|---|
| `Sin técnico` | `!ticket.technician` | Warning color, wrench icon |
| `Sin diagnóstico` | `status === 'EN_REVISION' && !ticket.diagnostic_notes` | Muted alert icon |
| `Vencido` | Active status && `created_at` older than 72h | Danger color, clock icon |
| `Listo sin retirar` | `status === 'LISTO_PARA_RETIRAR'` | Info color, package icon |
| `Esperando aprobación` | `status === 'ESPERANDO_APROBACION'` | Amber color, hourglass icon |

These are pure frontend computations — no backend changes required. The `created_at` field is already present in `TicketListResponse`.

### 2.4 Contextual Smart Actions

Replace the generic footer pattern with a single primary action button that adapts to the ticket's operational state:

| Ticket state | Smart action | Behavior |
|---|---|---|
| No technician assigned | **Asignar** | Opens detail modal focused on technician dropdown |
| `EN_REVISION` + no diagnostic | **Diagnosticar** | Opens `DiagnosticModal` directly |
| `ESPERANDO_APROBACION` | **WhatsApp: Seguimiento** | Pre-filled message asking about budget approval |
| `LISTO_PARA_RETIRAR` | **WhatsApp: Retiro** | Pre-filled message notifying equipment is ready |
| Default | **Ver detalle** | Opens detail modal |

The status select dropdown and save button remain available but are deprioritized visually (smaller, secondary).

### 2.5 Network Optimization

Remove the `useEffect` at line 77-94 of `AdminTicketCard.jsx` that fetches evidences on mount. Evidence loading moves exclusively into the detail modal's `useQuery` (already gated by `enabled: showDetail` at line 45-54). This eliminates 15 concurrent `GET /tickets/{id}/evidences` requests per page load.

### 2.6 Date Utilities

Add two functions to [`src/utils/date.js`](file:///C:/Users/cntmi/Desktop/Tecnidesk/frontend/src/utils/date.js):
- `formatRelativeAge(isoDate)`: Returns "Hoy", "Ayer", "Hace 2 días", "Hace 1 sem", etc.
- `isTicketStale(created_at, status)`: Returns `true` if the ticket has been in an active state for more than 72 hours. Used by the "Vencido" badge.

### 2.7 Backend: `filter_group` Parameter

A single addition to [`ticket_service.py`](file:///C:/Users/cntmi/Desktop/Tecnidesk/backend/app/services/ticket_service.py) `list_tickets()` and the corresponding router: accept an optional `filter_group` query parameter. When `filter_group=activos`, apply `Ticket.status.not_in([LISTO_PARA_RETIRAR, NO_APROBADO])` — mirroring the exact logic used by `get_ticket_stats()` for the "activos" count. This ensures the filtered list matches the KPI number exactly.

---

## 3. Capabilities

| Capability | Description |
|---|---|
| `workbench-card-declutter` | Reduce ticket card to operational essentials; relocate PII and detail to modal |
| `workbench-kpi-filters` | Transform KPI stat blocks into interactive filter toggles with backend `filter_group` support |
| `workbench-exception-badges` | Frontend-computed visual alerts for unassigned, stale, missing-diagnosis, and pending-pickup tickets |
| `workbench-smart-actions` | Contextual primary action button per ticket state |
| `workbench-network-optimization` | Eliminate N+1 evidence fetching on card mount |

---

## 4. Explicit Boundaries & Out of Scope

- **No Kanban view**: Column-based layout is deferred to a future phase pending validation that the list-based workbench does not already solve the prioritization problem.
- **No backend state-transition rules**: Business logic enforcement (e.g. "cannot move to EN_REPARACION without technician") is planned for Phase 2 and not included here.
- **No audit log / history table**: Status change history tracking is Phase 2 scope.
- **No drag-and-drop**: Not applicable to the list view.
- **No SLA configuration**: The 72h threshold for "Vencido" is hardcoded as a sensible default. Configurable SLA per shop is Phase 2+.
- **No new backend endpoints**: Only one new query parameter (`filter_group`) added to the existing `GET /tickets` endpoint.

---

## 5. Acceptance Criteria

1. The 4 KPI blocks at the top of `AdminDashboard.jsx` are clickable. Clicking "En taller" filters the ticket list to show only active tickets, and the count displayed matches the filtered result count exactly.
2. Each `AdminTicketCard` in the list view shows: device name/brand, tracking code, client name, relative age, status badge, technician name (or "Sin técnico" warning), and applicable exception badges — nothing else.
3. Email, phone number, PIN, full issue description, evidence gallery, and parts selector are only visible inside the detail modal.
4. Zero `GET /tickets/{id}/evidences` requests fire on page load or page navigation. Evidence requests only fire when the detail modal opens.
5. Each card shows exactly one contextual smart-action button that matches the ticket's current operational state.
6. A ticket with `created_at` older than 72 hours in an active status displays the "Vencido" badge.
7. All existing functionality (create ticket, assign technician, change status, submit diagnostic, upload evidence) continues to work without regression via the detail modal.
