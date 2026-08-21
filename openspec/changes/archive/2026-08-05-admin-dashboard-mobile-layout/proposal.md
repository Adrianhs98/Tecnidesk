## Intent

The Admin Dashboard is currently unoptimized for mobile screens, causing horizontal overflow and content overlap issues. This change aims to make the dashboard responsive, providing a usable experience on mobile devices (<= 768px) without breaking the desktop layout.

## Scope

### In Scope
- Stack the `.nav-pill` navigation vertically on screens <= 768px.
- Dynamically adjust `.workbench-layout` padding-top to prevent content overlap from the stacked navigation.
- Expand `.workbench-toolbar` search and filter inputs to 100% width on screens <= 480px.

### Out of Scope
- Redesigning the desktop layout or navigation behavior.
- Adding new dashboard features or metrics.
- Changes to other pages in the application.

## Capabilities

> This section is the CONTRACT between proposal and specs phases.
> The sdd-spec agent reads this to know exactly which spec files to create or update.
> Research `openspec/specs/` before filling this in.

### New Capabilities
None

### Modified Capabilities
None

## Approach

Implement a CSS-only solution (Option B from exploration):
1. Add media queries (`@media (max-width: 768px)`) in `App.css` to change `.nav-pill` to `flex-direction: column`.
2. Adjust the `padding-top` of `.workbench-layout` within the same media query to accommodate the taller, stacked `.nav-pill`.
3. Add media queries (`@media (max-width: 480px)`) to set width of `.workbench-toolbar` inputs to 100%.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `frontend/src/App.css` | Modified | Added media queries for `.nav-pill`, `.workbench-layout`, and `.workbench-toolbar` |
| `frontend/src/features/admin/AdminDashboard.jsx` | Modified | Potential minor class adjustments if needed (expected CSS only) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Mobile CSS breaks desktop layout | Low | Use `max-width` media queries strictly isolated from default desktop styles. |
| Overlapping elements on intermediate screen sizes | Medium | Test layout responsiveness across various breakpoints (480px, 768px, 1024px). |

## Rollback Plan

Revert the PR containing the `App.css` and `AdminDashboard.jsx` changes. Since this is a pure UI change, there are no database migrations or data corruption risks to mitigate during rollback.

## Dependencies

- None

## Success Criteria

- [ ] `.nav-pill` items stack vertically and do not overflow horizontally on screens <= 768px.
- [ ] Dashboard content (`.workbench-layout`) does not overlap with the navigation on any screen size.
- [ ] Toolbar inputs stretch to 100% width on screens <= 480px.

## Proposal question round

- Are there specific mobile devices or viewport sizes we must strictly target (e.g., iPhone SE, Galaxy Fold)?
- Should the `.nav-pill` turn into a hamburger menu or dropdown on mobile instead of just stacking, which might take up too much vertical space?
- Are there any other dashboard elements that currently behave poorly on mobile that we should include in this scope?
