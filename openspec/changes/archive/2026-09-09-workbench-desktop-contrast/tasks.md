# Tasks: Workbench Desktop Width & Ticket Card Contrast

## 1. Implementation
- [x] 1.1 Update `.workbench-canvas` in `frontend/src/App.css` with `max-width: 1500px` and `margin: 0 auto` for the desktop breakpoint
- [x] 1.2 Update `.ticket-card` in `frontend/src/App.css` to use `background: var(--bg-surface)` and contrast box-shadow
- [x] 1.3 Update `.tech-ticket-card` in `frontend/src/App.css` to use `background: var(--bg-surface)` and contrast box-shadow
- [x] 1.4 Add light theme elevation rule (`[data-theme="light"] .ticket-card, [data-theme="light"] .tech-ticket-card`) with `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)`

## 2. Verification & Regression
- [x] 2.1 Run Vitest test suite (`npm test -- --run`) in `frontend` to confirm no regressions or broken card tests
- [x] 2.2 Confirm responsive media queries for mobile and tablet remain intact
