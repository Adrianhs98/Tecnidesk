# Tasks: Workbench Operativo (Fase 3: Vista Kanban / Tablero de Columnas)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~350-390 lines |
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
| 1 | Complete Kanban Board View Integration | PR 1 | `npm test frontend/src/tests/features/KanbanBoard.test.jsx` | `npm run dev` and navigate to `/admin` dashboard | Revert `AdminDashboard.jsx` toggle, delete `Kanban*.jsx` components and tests |

## Phase 1: CSS Framework & Styling

- [x] 1.1 Add `.view-mode-toggle` styles to [App.css](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/App.css) for segmented list/kanban switch buttons.
- [x] 1.2 Add `.kanban-board-container`, `.kanban-columns-track`, and `.kanban-column` styles in [App.css](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/App.css) with horizontal overflow scrolling.
- [x] 1.3 Add `.kanban-column-header`, `.kanban-count-badge`, and `.kanban-ticket-card` density styles with SLA badge indicators in [App.css](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/App.css).

## Phase 2: Kanban Component Architecture

- [x] 2.1 Create [KanbanTicketCard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/KanbanTicketCard.jsx) rendering device info, client, relative age, technician pill, and quick advance button.
- [x] 2.2 Create [KanbanColumn.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/KanbanColumn.jsx) rendering column header, color accent, counter badge, and scrollable card list.
- [x] 2.3 Create [KanbanBoard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/KanbanBoard.jsx) defining `KANBAN_COLUMNS` and grouping tickets using `useMemo`.

## Phase 3: Integration into AdminDashboard

- [x] 3.1 Initialize `viewMode` state from `localStorage.getItem("tecnidesk_workbench_view")` in [AdminDashboard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/AdminDashboard.jsx).
- [x] 3.2 Add View Switcher toolbar toggle (List vs Kanban) with persistence to `localStorage` in [AdminDashboard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/AdminDashboard.jsx).
- [x] 3.3 Render `<KanbanBoard />` conditionally when `viewMode === 'kanban'`, passing filtered tickets and modal/status handlers in [AdminDashboard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/AdminDashboard.jsx).

## Phase 4: Assignment Guard Interception & Quick Transitions

- [x] 4.1 Implement `NEXT_STATUS_MAP` and advance handler in [KanbanBoard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/KanbanBoard.jsx).
- [x] 4.2 Intercept transition to `EN_REPARACION` when `technician` is missing and trigger diagnostic/assignment modal in [KanbanBoard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/KanbanBoard.jsx).
- [x] 4.3 Trigger `onStatusChange` optimistic updates on successful advance transitions in [KanbanBoard.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/KanbanBoard.jsx).

## Phase 5: Testing & Verification

- [x] 5.1 Create [KanbanBoard.test.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/tests/features/KanbanBoard.test.jsx) testing 5-column ticket bucketing and counter badges.
- [x] 5.2 Add tests for `localStorage` persistence and toggle switching in [KanbanBoard.test.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/tests/features/KanbanBoard.test.jsx).
- [x] 5.3 Add tests for unassigned technician guard interception when advancing to `EN_REPARACION` in [KanbanBoard.test.jsx](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/tests/features/KanbanBoard.test.jsx).
- [x] 5.4 Run `npm test frontend/src/tests/features/KanbanBoard.test.jsx` to verify all tests pass.
