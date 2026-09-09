# Specification: Workbench Desktop Width & Ticket Card Contrast

## Capability: workbench-desktop-contrast
Defines presentation constraints for the workbench container and elevated card visual hierarchy across dark and light themes.

### Requirement: Desktop Workbench Max-Width Constraint
The primary workbench canvas container (`.workbench-canvas`) MUST be constrained to a maximum width of `1500px` and centered with `margin: 0 auto` on desktop viewports, without altering lateral padding or mobile/tablet media queries.

#### Scenario: Desktop canvas is capped at 1500px and centered
- **Given** a user views `AdminDashboard` on a desktop screen (viewport width >= 1024px)
- **When** the page renders `.workbench-canvas`
- **Then** `max-width` is `1500px`
- **And** `margin` is `0 auto`
- **And** existing lateral padding (32px) is preserved

#### Scenario: Mobile and tablet breakpoints remain unaffected
- **Given** a user views `AdminDashboard` on a viewport <= 768px
- **When** the layout responds
- **Then** the workbench canvas continues to fill the available width seamlessly

---

### Requirement: Card Background Contrast
Ticket cards (`.ticket-card` and `.tech-ticket-card`) MUST use `var(--bg-surface)` to establish a distinct OKLCH lightness delta against both the page background (`--bg-canvas`) and container background (`--bg-paper`).

#### Scenario: Ticket cards use elevated surface background in dark mode
- **Given** the active theme is dark (default)
- **When** `.ticket-card` or `.tech-ticket-card` renders
- **Then** its background is `var(--bg-surface)` (`oklch(25% 0.02 260)`)
- **And** it is visibly lighter than `.workbench-canvas` (`oklch(20% 0.015 260)`)

#### Scenario: Ticket cards use elevated surface background in light mode
- **Given** the active theme is light (`[data-theme="light"]`)
- **When** `.ticket-card` or `.tech-ticket-card` renders
- **Then** its background is `var(--bg-surface)` (`oklch(91% 0.015 75)`)
- **And** it is distinctly separated from the container background (`oklch(94% 0.012 75)`)

---

### Requirement: Card Elevation Box Shadow
Ticket cards MUST have an elevation box shadow with subtle layering.

#### Scenario: Ticket cards receive elevation shadow in light mode
- **Given** the active theme is light (`[data-theme="light"]`)
- **When** `.ticket-card` or `.tech-ticket-card` renders
- **Then** its box shadow includes `0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)`

#### Scenario: Ticket cards receive contrast shadow in dark mode
- **Given** the active theme is dark (default)
- **When** `.ticket-card` or `.tech-ticket-card` renders
- **Then** its box shadow provides subtle depth separation (`0 1px 3px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.15)`)
