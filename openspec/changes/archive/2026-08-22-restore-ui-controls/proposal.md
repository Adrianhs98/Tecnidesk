## Intent

Restore essential UI controls that were temporarily hidden for screenshots, specifically the dynamic shop name in the top navbar and the pagination limit selector in the admin dashboard, to ensure full application functionality for users.

## Scope

### In Scope
- Inject the dynamic business name (`sessionStorage.getItem("td_shop")`) into the top navbar (replacing the hardcoded "TecniDesk Admin").
- Restore the pagination limit `<select>` control in `AdminDashboard.jsx` using the existing `limit` and `setLimit` state.

### Out of Scope
- Adding new pagination features beyond the existing limit selection.
- Modifying backend responses or authentication flow.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- None

## Approach

- Modify the Top Navbar component to read `sessionStorage.getItem("td_shop")` and display it instead of the hardcoded "TecniDesk Admin". Add a fallback to "TecniDesk Admin" if the item is missing.
- Modify `AdminDashboard.jsx` to render the `<select>` element for "Límite por página", binding its value to the existing `limit` state and its `onChange` event to update the state.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/pages/LoginPage.jsx` / Navbar | Modified | Update hardcoded shop name to dynamic value from session storage |
| `src/pages/AdminDashboard.jsx` | Modified | Restore pagination limit selector dropdown |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Missing `td_shop` in sessionStorage | Low | Provide a fallback default name ("TecniDesk Admin"). |
| Layout shifts when restoring the limit selector | Low | Test the dashboard view with the restored control to ensure it fits the existing UI layout. |

## Rollback Plan

Revert the file changes in `AdminDashboard.jsx` and the Navbar to their previous state where the UI elements were hidden/hardcoded.

## Dependencies

- None

## Success Criteria

- [ ] The top navbar displays the actual business name fetched from `sessionStorage`.
- [ ] Users can change the pagination limit (e.g., 10, 15, 20) in the admin dashboard via the dropdown.
- [ ] Changing the limit correctly updates the displayed data.
