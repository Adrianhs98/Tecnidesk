# Proposal: Workbench Desktop Width & Ticket Card Contrast

## Problem
1. **Excessive Desktop Workbench Width**: In `AdminDashboard.jsx` and `App.css`, `.workbench-canvas` is capped at `max-width: 1600px`, causing excess whitespace, wide stat card stretching, and visual disconnection between toolbar filters and ticket cards on widescreen monitors.
2. **Insufficient Card/Background Contrast**: The `.ticket-card` (and `.tech-ticket-card` in the technician view) currently inherits `background: var(--surface)` / `var(--bg-paper)`. Because the `.workbench-canvas` container itself has `background: var(--bg-paper)`, ticket cards share the exact same background color as the surrounding canvas, blending into the page with only a hairline border separating them.
3. **Missing Card Elevation**: In light mode, cards lack subtle elevation shadows (`box-shadow: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04)`), diminishing the perception of depth and tactile structure.

## Solution
1. **Constrain Desktop Workbench Container**:
   - Update `.workbench-canvas` in `frontend/src/App.css` to `max-width: 1500px` and `margin: 0 auto` for the desktop breakpoint, preserving existing lateral padding and all mobile/tablet media queries unchanged.
2. **Elevate Ticket Card Background Contrast**:
   - Update `.ticket-card` and `.tech-ticket-card` background to `var(--bg-surface)`. In dark mode (`oklch(25% 0.02 260)` vs `20%` paper), this provides a +5% lightness lift. In light mode (`oklch(91% 0.015 75)` vs `94%` paper and `97%` canvas), this provides distinct visual grounding using established theme tokens.
3. **Add Elevation Shadow**:
   - Apply elevation shadow `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.15)` in dark mode.
   - In light mode (`[data-theme="light"]`), apply `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)`.
   - Preserve border-radius, padding, and grid gaps.

## Capabilities
### New Capabilities
- `workbench-desktop-contrast`: Desktop layout width constraint for the workbench canvas and elevated card contrast with theme-aware shadows.

## Impact
- **Modified Files:**
  - `frontend/src/App.css`
- **Dependencies:** None.
- **Breaking Changes:** None. Purely visual enhancement preserving responsive layout on mobile/tablet.
