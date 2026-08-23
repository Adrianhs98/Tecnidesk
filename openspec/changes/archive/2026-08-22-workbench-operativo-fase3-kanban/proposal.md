# Proposal: Workbench Operativo (Fase 3: Vista Kanban / Tablero de Columnas)

## Intent

While the list view provides tabular operational data, workshop managers and technicians need a panoramic visual pipeline of all equipment organized by operational stages. Phase 3 introduces a lightweight, responsive Kanban board view alongside the existing list view in `AdminDashboard.jsx`, enabling at-a-glance workload visualization, bottleneck identification, and fast status transitions with strict guard enforcement.

## Scope

### In Scope
- **View Switcher & State Persistence**: Toggle button (List vs Kanban) in workbench toolbar persisted in `localStorage` (`workbench_view_mode`).
- **5-Column Pipeline Grouping**: Categorized columns for workshop workflow:
  1. *Recepción / Ingreso* (`EN_ESPERA_INGRESO`, `RECIBIDO`)
  2. *En Revisión & Diagnóstico* (`EN_REVISION`)
  3. *Presupuesto & Espera* (`ESPERANDO_APROBACION`, `ESPERANDO_REPUESTO`)
  4. *En Reparación* (`EN_REPARACION`)
  5. *Listos para Entrega* (`LISTO_PARA_RETIRAR`)
- **Compact Kanban Card (`KanbanTicketCard`)**: Dense card showing device brand/model, client name, age, technician badge (warning if unassigned), dynamic SLA alert, and quick transition actions.
- **Fast Status Transitions & Phase 2 Guards**: Quick advance buttons triggering status updates while respecting technician assignment guards.
- **Responsive Board Layout**: Horizontally scrollable column container with column counters and sticky headers.

### Out of Scope
- Custom user-created or tenant-configurable columns (columns map directly to system status enums).
- Heavy external drag-and-drop npm dependencies (use native HTML5 drag-and-drop or direct action buttons to preserve lightweight bundle size).
- Archiving completed/delivered tickets from the board (handled in separate lifecycle phase).

## Capabilities

### New Capabilities
- `kanban-view-toggle`: View switcher in `AdminDashboard.jsx` allowing seamless toggling between List and Kanban views, persisted in `localStorage`.
- `kanban-board-columns`: 5-column operational grouping mapping workshop lifecycle statuses with real-time ticket counters.
- `kanban-ticket-card`: High-density ticket card presenting device info, technician assignment status, dynamic SLA warnings, and action triggers.
- `kanban-status-transition`: Interactive status transition handlers enforcing assignment validation guards before advancing to active repair.
- `kanban-responsive-layout`: CSS-driven responsive column board supporting horizontal scrolling on tablet and desktop screens.

### Modified Capabilities
None

## Approach

1. **Dashboard View Integration**: Add view mode state (`'list' | 'kanban'`) to `AdminDashboard.jsx`, initializing from and syncing to `localStorage.getItem('workbench_view_mode')`.
2. **Kanban Board Component**: Create `KanbanBoard.jsx` and `KanbanColumn.jsx` under `frontend/src/features/admin/components/`. Categorize fetched tickets into the 5 semantic column buckets.
3. **Card & Actions**: Build `KanbanTicketCard.jsx` displaying compact ticket metadata, SLA badges (via `date.js`), and quick advance buttons.
4. **Transition Guards**: Ensure transitions to `EN_REPARACION` verify technician assignment or open the technician assignment modal.
5. **Styling & Testing**: Add responsive CSS rules in `src/styles/admin.css` and comprehensive unit/render tests in Vitest.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/features/admin/AdminDashboard.jsx` | Modified | Add view switcher toggle, state persistence, and conditional board rendering |
| `frontend/src/features/admin/components/KanbanBoard.jsx` | New | Main board container managing columns and grouped tickets |
| `frontend/src/features/admin/components/KanbanColumn.jsx` | New | Individual stage column with header, counters, and ticket list |
| `frontend/src/features/admin/components/KanbanTicketCard.jsx` | New | High-density ticket card with SLA and quick advance buttons |
| `frontend/src/styles/admin.css` | Modified | Styles for Kanban layout, columns, cards, and view toggle |
| `frontend/src/tests/features/KanbanBoard.test.jsx` | New | Unit and interaction tests for Kanban board and transitions |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Pagination limit truncating tickets across columns in Kanban mode | Med | Fetch a larger operational batch or adjust query limit when Kanban view is active |
| Unassigned technician transitions blocked by Phase 2 backend guards | Low | Prompt technician assignment modal when advancing to `EN_REPARACION` |
| Horizontal overflow on smaller screens | Low | Implement CSS touch/wheel smooth scrolling with min-width columns |

## Rollback Plan

1. Revert `AdminDashboard.jsx` to list-only rendering.
2. Remove newly added `KanbanBoard.jsx`, `KanbanColumn.jsx`, `KanbanTicketCard.jsx`, and test files.
3. Revert Kanban-specific styles in `src/styles/admin.css`.

## Dependencies

- Phase 2 backend status transition guards and dynamic SLA calculations.

## Success Criteria

- [ ] Users can toggle between List and Kanban views with persistence across page reloads.
- [ ] Tickets are categorized correctly into the 5 semantic status columns with accurate count badges.
- [ ] Kanban cards clearly display device info, client name, technician assignment, and SLA warnings.
- [ ] Quick advance actions update ticket status and trigger optimistic UI updates.
- [ ] Transitions to `EN_REPARACION` require an assigned technician.
- [ ] All Vitest test suites pass with 100% green status.
