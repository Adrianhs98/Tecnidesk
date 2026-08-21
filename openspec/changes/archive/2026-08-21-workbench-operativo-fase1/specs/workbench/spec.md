# Specification: Workbench Operativo Mínimo

**Capability**: `workbench-operativo-fase1`  
**Status**: draft  
**Version**: 1.0  
**Proposal**: [`proposal.md`](../proposal.md)

## Overview
This capability transforms the TecniDesk admin dashboard from a flat, data-heavy paginated list into an operational workbench. The change is purely additive on the frontend and requires one minimal backend addition (`filter_group` query parameter). All existing functionality is preserved and accessible via the detail modal.

---

## Scenarios

### Feature: workbench-card-declutter

#### Scenario 1: Ticket card surface shows only operational essentials
**Given** the admin is viewing the ticket list  
**When** a ticket card is rendered  
**Then** the card surface displays: `device_brand`, `device_model`, masked `tracking_token`, `customer.full_name`, relative age (e.g. "Hace 2 días"), status badge, and technician name or "Sin técnico" warning  
**And** the card does NOT display: customer email, customer phone number, PIN badge, issue description text, absolute date string, evidence count, or diagnostic notes preview  

#### Scenario 2: Clicking "Ver detalle" opens the full modal
**Given** a ticket card is rendered in the list  
**When** the user clicks "Ver detalle"  
**Then** the detail modal opens  
**And** the modal displays all previously surfaced fields: customer PII (with visibility toggle), PIN, full issue description, diagnostic notes, evidence gallery, parts selector, technician assignment dropdown, and status history  

#### Scenario 3: No evidences request fires on card mount
**Given** the admin navigates to the dashboard or changes page  
**When** the ticket list renders  
**Then** zero `GET /tickets/{id}/evidences` requests are made  
**And** evidence requests only fire after the user opens a specific ticket's detail modal  

---

### Feature: workbench-kpi-filters

#### Scenario 4: KPI block is clickable and applies a filter
**Given** the admin is viewing the dashboard with the "Total equipos" KPI showing 42 tickets  
**When** the admin clicks the "Listos" KPI block  
**Then** the ticket list reloads showing only tickets with `status = LISTO_PARA_RETIRAR`  
**And** the "Listos" KPI block displays an active visual state (accent border and background)  
**And** pagination resets to page 1  

#### Scenario 5: "En taller" filter matches the KPI count exactly
**Given** the `GET /tickets/stats` endpoint returns `activos: 18`  
**When** the admin clicks the "En taller" KPI block  
**Then** the list fetches `GET /tickets?filter_group=activos`  
**And** the `filter_group=activos` backend filter applies `status NOT IN (LISTO_PARA_RETIRAR, NO_APROBADO)` — the identical logic used to compute the "activos" stat  
**And** the total count displayed in the paginator matches 18  

#### Scenario 6: Clicking an active KPI clears the filter
**Given** the "Listos" KPI block is currently active and filtering the list  
**When** the admin clicks the "Listos" KPI block again  
**Then** the filter is cleared  
**And** the ticket list reloads showing all tickets  
**And** all KPI blocks return to their inactive visual state  

#### Scenario 7: KPI filter coexists with search and date filters
**Given** the admin has typed "Apple" in the search box  
**When** the admin also clicks the "En espera" KPI block  
**Then** the ticket list fetches `GET /tickets?search=Apple&ticket_status=EN_ESPERA_INGRESO`  
**And** only tickets matching both conditions are shown  

---

### Feature: workbench-exception-badges

#### Scenario 8: "Sin técnico" badge appears on unassigned tickets
**Given** a ticket exists where `ticket.technician` is `null`  
**When** the ticket card renders  
**Then** a "Sin técnico" badge is visible on the card surface with warning styling  

#### Scenario 9: "Sin diagnóstico" badge appears during revision without notes
**Given** a ticket exists where `status === 'EN_REVISION'` and `diagnostic_notes` is `null` or empty  
**When** the ticket card renders  
**Then** a "Sin diagnóstico" badge is visible on the card surface  

#### Scenario 10: "Vencido" badge appears on stale active tickets
**Given** a ticket exists with an active status (not `LISTO_PARA_RETIRAR` or `NO_APROBADO`)  
**And** the ticket's `created_at` is more than 72 hours ago  
**When** the ticket card renders  
**Then** a "Vencido" badge is visible with danger styling  

#### Scenario 11: "Listo sin retirar" badge appears on ready tickets
**Given** a ticket exists where `status === 'LISTO_PARA_RETIRAR'`  
**When** the ticket card renders  
**Then** a "Listo sin retirar" badge is visible on the card surface with info styling  

#### Scenario 12: "Esperando aprobación" badge appears on pending approval tickets
**Given** a ticket exists where `status === 'ESPERANDO_APROBACION'`  
**When** the ticket card renders  
**Then** an "Esperando aprobación" badge is visible on the card surface with amber styling  

#### Scenario 13: No exception badge appears on a healthy ticket
**Given** a ticket exists where: technician is assigned, status is `EN_REPARACION`, `diagnostic_notes` is populated, and `created_at` is less than 72 hours ago  
**When** the ticket card renders  
**Then** no exception badges are displayed  

---

### Feature: workbench-smart-actions

#### Scenario 14: Unassigned ticket shows "Asignar" as primary action
**Given** a ticket exists where `ticket.technician` is `null`  
**When** the ticket card renders  
**Then** the primary action button reads "Asignar"  
**And** clicking it opens the detail modal with focus on the technician assignment section  

#### Scenario 15: EN_REVISION ticket without diagnosis shows "Diagnosticar"
**Given** a ticket exists where `status === 'EN_REVISION'` and `diagnostic_notes` is `null`  
**When** the ticket card renders  
**Then** the primary action button reads "Diagnosticar"  
**And** clicking it opens the `DiagnosticModal` directly  

#### Scenario 16: ESPERANDO_APROBACION ticket shows WhatsApp follow-up action
**Given** a ticket exists where `status === 'ESPERANDO_APROBACION'`  
**When** the ticket card renders  
**Then** the primary action button reads "WhatsApp: Seguimiento"  
**And** clicking it opens WhatsApp with a pre-filled message requesting a budget approval response  

#### Scenario 17: LISTO_PARA_RETIRAR ticket shows WhatsApp pickup action
**Given** a ticket exists where `status === 'LISTO_PARA_RETIRAR'`  
**When** the ticket card renders  
**Then** the primary action button reads "WhatsApp: Retiro"  
**And** clicking it opens WhatsApp with a pre-filled message informing the client their device is ready  

#### Scenario 18: Default ticket shows "Ver detalle"
**Given** a ticket exists that does not match any of the above priority conditions  
**When** the ticket card renders  
**Then** the primary action button reads "Ver detalle"  
**And** clicking it opens the detail modal  

---

### Feature: workbench-network-optimization

#### Scenario 19: Evidence requests are lazy-loaded per modal
**Given** a page renders 15 ticket cards  
**When** the admin opens the detail modal for exactly one ticket  
**Then** exactly one `GET /tickets/{id}/evidences` request fires (for that specific ticket)  
**And** no other evidence requests have fired for the remaining 14 cards  

#### Scenario 20: Evidence data loads correctly inside the modal
**Given** the admin has opened a specific ticket's detail modal  
**When** the modal's evidence section renders  
**Then** the evidence photos for that ticket are displayed correctly  
**And** the "Agregar evidencia" upload control is functional  

---

### Feature: Backend filter_group parameter

#### Scenario 21: filter_group=activos filters by the correct status set
**Given** the backend `GET /tickets` endpoint is called with `filter_group=activos`  
**When** `ticket_service.list_tickets()` processes the request  
**Then** the SQL query applies `Ticket.status.not_in([LISTO_PARA_RETIRAR, NO_APROBADO])`  
**And** the returned tickets match exactly the same universe counted by `get_ticket_stats()` under the "activos" key  

#### Scenario 22: filter_group is ignored when ticket_status is also provided
**Given** the backend `GET /tickets` endpoint is called with both `ticket_status=EN_REVISION` and `filter_group=activos`  
**When** `ticket_service.list_tickets()` processes the request  
**Then** `ticket_status` takes precedence and `filter_group` is ignored  
**And** only `EN_REVISION` tickets are returned  

---

### Feature: Date utilities

#### Scenario 23: formatRelativeAge returns human-readable elapsed time
**Given** a ticket `created_at` ISO timestamp  
**When** `formatRelativeAge(created_at)` is called  
**Then** it returns "Hoy" for timestamps within the current calendar day  
**And** "Ayer" for timestamps from the previous calendar day  
**And** "Hace N días" for timestamps 2–29 days ago (where N is the day count)  
**And** "Hace N sem" for timestamps 30+ days ago  

#### Scenario 24: isTicketStale correctly identifies stale active tickets
**Given** a ticket's `created_at` and `status`  
**When** `isTicketStale(created_at, status)` is called  
**Then** it returns `true` if `status` is not in `[LISTO_PARA_RETIRAR, NO_APROBADO]` AND the elapsed time since `created_at` exceeds 72 hours  
**And** it returns `false` for closed, rejected, or tickets younger than 72 hours  
