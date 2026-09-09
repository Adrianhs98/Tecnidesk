# Design: Workbench Desktop Width & Ticket Card Contrast

## Architecture & Context
TecniDesk employs an OKLCH color space architecture defined via CSS variables in `frontend/src/App.css`. Theme switching between dark mode (default) and light mode (`[data-theme="light"]`) is orchestrated through `ThemeContext.jsx` and persisted in `localStorage`.

The main operational workspace is the "Workbench", structured with a floating navigation pill (`.nav-pill`), an encompassing page background (`.workbench-layout` with `var(--bg-canvas)`), and a centralized workbench canvas (`.workbench-canvas` with `var(--bg-paper)`). Within this canvas sit stat cards, search/filters toolbar, and the ticket card grid (`.ticket-card`).

## Decisions & Tradeoffs
1. **Desktop Container Constraint (`.workbench-canvas`):**
   - *Decision:* In the base desktop definition of `.workbench-canvas`, update `max-width: 1600px` to `max-width: 1500px; margin: 0 auto;`.
   - *Why:* Keeps content visually compact and cohesive on widescreen displays without modifying any responsive media query (`<= 768px`, `<= 600px`, `<= 480px`).
   - *Tradeoff:* Slightly less horizontal width on 4K monitors, but significantly improves information density and readability.

2. **Semantic Elevation using Existing OKLCH Tokens (`var(--bg-surface)`):**
   - *Decision:* Change card background from `var(--surface)` / `var(--bg-paper)` to `var(--bg-surface)`.
   - *Why:* Respects the design system rule ("no hardcoded colors outside defined OKLCH tokens"). In dark mode, `--bg-surface` provides a +5% lightness delta (`oklch(25% ...)` vs `oklch(20% ...)` of paper canvas). In light mode, `--bg-surface` provides a -3% depth delta (`oklch(91% ...)` vs `oklch(94% ...)` of paper canvas).

3. **Subtle Elevation Box Shadows:**
   - *Decision:*
     - Dark mode default: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.15);`
     - Light mode: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);`
     - Keep hover states intact with smooth transitions.

## File Changes
- **`frontend/src/App.css`**:
  - Update `.workbench-canvas` rule (`max-width: 1500px; margin: 0 auto;`).
  - Update `.ticket-card` background and box-shadow.
  - Update `.tech-ticket-card` background and box-shadow.
  - Add `[data-theme="light"] .ticket-card` and `[data-theme="light"] .tech-ticket-card` shadow rules.
