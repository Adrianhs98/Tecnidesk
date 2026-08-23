# Design: Workbench Operativo (Fase 3: Vista Kanban / Tablero de Columnas)

## Technical Approach

Introduce a responsive, multi-column Kanban view (`KanbanBoard`) alongside the existing tabular grid in `AdminDashboard.jsx`. A view toggle controls `viewMode` (`'list' | 'kanban'`), persisted in `localStorage`. The board groups tickets into 5 semantic workflow columns, rendering high-density `KanbanTicketCard` components with SLA warning badges, technician pills, and quick advance triggers guarded by Phase 2 assignment rules.

## Architecture Decisions

### Decision: State Management & View Persistence

| Option | Tradeoff | Decision |
|---|---|---|
| URL Query Param (`?view=kanban`) | Shareable URLs, but alters browser history on simple view toggles | Rejected |
| `localStorage` (`tecnidesk_workbench_view`) + React State | Fast instant toggle, persistent per operator device without URL churn | **Selected** |

### Decision: Board Column Categorization

| Option | Tradeoff | Decision |
|---|---|---|
| Server-side column bucketing API | Requires new backend endpoint and duplicate queries | Rejected |
| Client-side `useMemo` grouping across 5 semantic buckets | Zero backend overhead; leverages existing React Query cache seamlessly | **Selected** |

### Decision: Phase 2 Assignment Guard Interception

| Option | Tradeoff | Decision |
|---|---|---|
| Fire PATCH and handle 400 backend error toast | Jarring UX; triggers unnecessary network round-trips | Rejected |
| Client-side guard intercepting transitions to `EN_REPARACION` | If `!ticket.technician`, intercepts advance and opens modal with assignment focus | **Selected** |

### Decision: Drag-and-Drop vs Quick Action Triggers

| Option | Tradeoff | Decision |
|---|---|---|
| Heavy DnD library (e.g., `@hello-pangea/dnd`) | Increases bundle size (~45KB) and introduces touch lag on tablets | Rejected |
| One-click advance buttons & detail click triggers | Instant responsive interaction on desktop/touch, zero dependency overhead | **Selected** |

## Data Flow

```
[localStorage / User Click] ──→ viewMode ('list' | 'kanban')
                                        │
┌───────────────────────────────────────┴──────────────────────────────────────┐
│ AdminDashboard (React Query: 'dashboardData')                                │
│   ├─ (viewMode === 'list')   ──→ <AdminTicketCard /> Grid + Pagination       │
│   └─ (viewMode === 'kanban') ──→ <KanbanBoard /> (5 Grouped Columns)         │
│                                    └─ <KanbanTicketCard />                   │
│                                         ├─ Click Card ──→ Open Detail Modal │
│                                         └─ Advance ───→ Check Guard         │
│                                                           ├─ Valid: PATCH   │
│                                                           └─ No Tech: Modal │
└──────────────────────────────────────────────────────────────────────────────┘
```

## File Changes

| File | Action | Description |
|---|---|---|
| `frontend/src/features/admin/AdminDashboard.jsx` | Modify | Add `viewMode` state, persistence, toolbar segmented toggle, and conditional `<KanbanBoard />` rendering. |
| `frontend/src/features/admin/components/KanbanBoard.jsx` | Create | 5-column container grouping tickets with column counters and responsive horizontal scroll. |
| `frontend/src/features/admin/components/KanbanColumn.jsx` | Create | Individual workflow column with sticky header, status counter badge, and scrollable card list. |
| `frontend/src/features/admin/components/KanbanTicketCard.jsx` | Create | High-density card displaying device, client, relative age, SLA alert, technician badge, and guarded advance action. |
| `frontend/src/App.css` | Modify | Styles for `.view-mode-toggle`, `.kanban-board-container`, `.kanban-column`, and `.kanban-ticket-card`. |
| `frontend/src/tests/features/KanbanBoard.test.jsx` | Create | Unit and interaction tests covering column grouping, guarded transitions, and view persistence. |

## Interfaces / Contracts

```typescript
type WorkbenchViewMode = 'list' | 'kanban';

interface KanbanColumnDef {
  id: string;
  title: string;
  statuses: string[];
  accentColor: string;
}

const KANBAN_COLUMNS: KanbanColumnDef[] = [
  { id: 'ingreso', title: 'Ingreso / Recepción', statuses: ['EN_ESPERA_INGRESO', 'RECIBIDO'], accentColor: 'var(--accent)' },
  { id: 'revision', title: 'En Revisión & Diagnóstico', statuses: ['EN_REVISION'], accentColor: '#B89251' },
  { id: 'espera', title: 'Presupuesto & Espera', statuses: ['ESPERANDO_APROBACION', 'ESPERANDO_REPUESTO'], accentColor: '#CC8F5A' },
  { id: 'reparacion', title: 'En Reparación', statuses: ['EN_REPARACION'], accentColor: '#6F9FCC' },
  { id: 'listos', title: 'Listo para Retirar', statuses: ['LISTO_PARA_RETIRAR'], accentColor: 'var(--success)' },
];

const NEXT_STATUS_MAP: Record<string, string> = {
  EN_ESPERA_INGRESO: 'EN_REVISION',
  EN_REVISION: 'ESPERANDO_APROBACION',
  ESPERANDO_APROBACION: 'EN_REPARACION',
  ESPERANDO_REPUESTO: 'EN_REPARACION',
  EN_REPARACION: 'LISTO_PARA_RETIRAR',
};
```

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | Ticket column categorization | Verify `KanbanBoard` correctly buckets tickets into 5 columns matching `KANBAN_COLUMNS`. |
| Unit | SLA & Stale calculation | Validate `isTicketStale` triggers visual overdue indicators in `KanbanTicketCard`. |
| Interaction | Guarded status advance | Assert advance to `EN_REPARACION` without technician opens assignment modal and prevents PATCH. |
| Interaction | View switcher persistence | Verify clicking toggle updates `localStorage("tecnidesk_workbench_view")` and view state. |

## Threat Matrix

`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.`

## Migration / Rollout

No database or backend migration required. The frontend defaults to `'list'` mode if no `localStorage` preference exists, ensuring complete backward compatibility.

## Open Questions

- None. Phase 2 assignment guards and dynamic SLA utilities (`isTicketStale`) are already available in the codebase.
