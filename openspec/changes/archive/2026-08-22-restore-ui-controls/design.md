## Technical Approach

The overall technical strategy is to restore previously hidden UI elements directly in `AdminDashboard.jsx`. Specifically, the top navigation pill will be updated to read the dynamic shop name from `sessionStorage`, and the pagination container will be updated to render a dropdown (`<select>`) that modifies the existing `limit` state. Both changes involve modifying existing state and markup in `AdminDashboard.jsx` without the need for architectural shifts.

## Architecture Decisions

### Decision: Navbar Dynamic Text Read Location

**Choice**: Read `sessionStorage.getItem("td_shop")` directly inline within the JSX render or via a simple variable declaration, falling back to "TecniDesk Admin".
**Alternatives considered**: Storing the shop name in a React context or Redux store.
**Rationale**: The shop name is set once during login. Reading directly from `sessionStorage` avoids boilerplate for such a simple read-only data point that doesn't change during the session.

### Decision: Pagination Limit State Binding

**Choice**: Use the existing `limit` state variable and map the `<select>` `onChange` event to `setLimit` (and reset `page` to 0).
**Alternatives considered**: Introducing a separate component for pagination.
**Rationale**: The pagination controls are already implemented inline within `AdminDashboard.jsx`. Modifying them directly is less invasive and perfectly maps to the proposal's scope.

## Data Flow

    [Session Storage] ──(read)──→ AdminDashboard.jsx (Navbar section)
    
    [<select> limit] ──(onChange)──→ setLimit(val) & setPage(0) ──→ useQuery refetch

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/features/admin/AdminDashboard.jsx` | Modify | Update `<span className="admin-title">TecniDesk Admin</span>` to use `{sessionStorage.getItem("td_shop") || "TecniDesk Admin"}`. Add a `<select>` dropdown next to the pagination controls to allow the user to change the `limit` state (e.g., 10, 15, 20, 50). |

## Interfaces / Contracts

No new interfaces or contracts are introduced.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit/Integration | Navbar Shop Name | Verify that the shop name renders correctly when `td_shop` is present in `sessionStorage`, and falls back to "TecniDesk Admin" when absent. |
| E2E | Pagination Limit | Test that changing the limit via the dropdown correctly triggers a network request with the new `limit` parameter and resets the pagination to the first page. |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required.

## Open Questions

- None
