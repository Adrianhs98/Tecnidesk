## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~20 lines |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single PR |
| Delivery strategy | exception-ok |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Restore UI controls | PR 1 | N/A | N/A | `frontend/src/features/admin/AdminDashboard.jsx` |

## Phase 1: Core Implementation

- [x] 1.1 In `frontend/src/features/admin/AdminDashboard.jsx`, update the `.admin-title` element to use `{sessionStorage.getItem("td_shop") || "TecniDesk Admin"}` instead of hardcoded text.
- [x] 1.2 In `frontend/src/features/admin/AdminDashboard.jsx`, restore the pagination limit `<select>` dropdown, mapping its `onChange` event to update the `limit` state and reset the `page` state to 0.

## Phase 2: Testing / Verification

- [x] 2.1 Manually verify that the shop name renders correctly when `td_shop` is present in `sessionStorage`, and falls back to "TecniDesk Admin" when absent.
- [x] 2.2 Manually verify that changing the limit via the dropdown in the admin dashboard correctly updates the displayed data and resets the page.
