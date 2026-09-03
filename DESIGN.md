# DESIGN.md — TecniDesk Design System

> **Style Paradigm:** Airtable-Inspired Workflow Utility  
> **Target Environment:** High-efficiency service management, retail counter, repair shop operations  
> **Core Objective:** Maximum readability and data density for non-technical users, clean data tables, structured forms, and immediate visual hierarchy without decorative clutter.

---

## 1. Visual Direction & Foundations

The TecniDesk interface follows an **Airtable-inspired design language**:
- **Canvas & Polarity:** Light UI canvas (`#ffffff` / `#f8fafc`) as default for ambient daytime lighting in retail and workshop counters, with a complete Dark Mode token spec (`[data-theme="dark"]`) for night shifts and low-light workbench environments.
- **Structural Framing:** Clean, hair-thin container borders (`#dddddd` in light, `#272d38` in dark) define content boundaries rather than dramatic drop shadows.
- **Visual Restraint:** The chrome remains neutral and quiet. Color is used strictly for functional status indicators, primary actions, and immediate alerts.
- **Density:** Medium-high operational density balancing touch and mouse targets while displaying comprehensive ticket tables and inspection forms.

---

## 2. Typography

We adopt **Inter** as the primary type family (with **Work Sans** as secondary alternative) to mirror the clarity and geometric balance of Neue Haas Grotesk.

| Role | Font Family | Size | Weight | Line Height | Tracking | WCAG AA / AAA Status |
|---|---|---|---|---|---|---|
| **Display / Page Title** | `Inter`, sans-serif | 24px (1.5rem) | 600 (SemiBold) | 1.25 | -0.02em | Pass AAA (`#181d26` on `#ffffff`: 15.6:1) |
| **Section Heading (H2)** | `Inter`, sans-serif | 18px (1.125rem) | 600 (SemiBold) | 1.3 | -0.01em | Pass AAA (`#181d26` on `#ffffff`: 15.6:1) |
| **Subsection (H3)** | `Inter`, sans-serif | 15px (0.9375rem) | 600 (SemiBold) | 1.4 | 0 | Pass AAA (`#181d26` on `#ffffff`: 15.6:1) |
| **Body (Default)** | `Inter`, sans-serif | 14px (0.875rem) | 400 (Regular) | 1.5 | 0 | Pass AAA (`#181d26` on `#ffffff`: 15.6:1) |
| **Body Strong** | `Inter`, sans-serif | 14px (0.875rem) | 500 (Medium) | 1.5 | 0 | Pass AAA (`#181d26` on `#ffffff`: 15.6:1) |
| **Caption / Labels (12px)** | `Inter`, sans-serif | 12px (0.75rem) | 500 (Medium) | 1.4 | +0.01em | **Pass AAA** (`#4b5563` on `#ffffff`: **7.56:1**) |
| **Tabular Figures** | `Inter`, monospace / `tabular-nums` | 13px (0.8125rem) | 400 / 500 | 1.4 | 0 | Pass AAA (`#181d26` on `#ffffff`: 15.6:1) |

> **Accessibility Note (WCAG 2.1 AA/AAA):**  
> For small 12px captions and metadata, `--color-ink-subtle` is calibrated to `#4b5563` (7.56:1 contrast ratio on white), strictly exceeding the 4.5:1 AA requirement and clearing the 7.0:1 AAA threshold to prevent legibility degradation on low-DPI counter screens.

---

## 3. Radii, Borders, Focus & Elevation

| Element | Value | CSS Token | Description |
|---|---|---|---|
| **Controls & Inputs** | `6px` | `--radius-sm` | Text fields, select dropdowns, search inputs, pills |
| **Cards & Modals** | `8px` | `--radius-md` | Container cards, modal windows, table wrappers |
| **Badges / Status Chips**| `6px` | `--radius-badge` | Soft rounded tags for quick status scannability |
| **Hairline Border** | `1px solid var(--color-hairline)` | `--border-hairline` | Standard divider for cards, table rows, and inputs |
| **Strong Border** | `1px solid var(--color-border-strong)` | `--border-strong` | Interactive input border |
| **Focus Ring (Tactile)** | `0 0 0 3px var(--color-focus-ring)` | `--focus-ring` | High-visibility ring with 18% opacity for touch & keyboard navigation |
| **Subtle Elevation** | `0 1px 3px rgba(0,0,0,0.06)` | `--shadow-sm` | Raised cards, dropdown menus |
| **Overlay Elevation** | `0 8px 24px rgba(0,0,0,0.12)` | `--shadow-lg` | Dialogs, slide-overs, and popovers |

---

## 4. Color Tokens (Dual Theme: Light & Dark)

### 4.1 Light Mode (Default Counter/Workbench Theme)

```css
:root,
[data-theme="light"] {
  /* Canvas & Surfaces */
  --color-canvas: #ffffff;
  --color-surface-soft: #f8fafc;
  --color-surface-subtle: #f1f3f5;
  --color-surface-hover: #f3f4f6;

  /* Ink & Typography */
  --color-ink: #181d26;             /* 15.6:1 ratio (AAA) - Primary text & titles */
  --color-ink-muted: #374151;       /* 9.54:1 ratio (AAA) - Body copy & secondary details */
  --color-ink-subtle: #4b5563;      /* 7.56:1 ratio (AAA) - Labels, timestamps, 12px captions */
  --color-ink-disabled: #9ca3af;    /* Inactive placeholders */

  /* Borders & Dividers */
  --color-hairline: #dddddd;        /* Default borders, table gridlines */
  --color-border-strong: #9297a0;   /* Interactive input border */
  --color-border-focus: #181d26;    /* Focused control outline */
  --color-focus-ring: rgba(24, 29, 38, 0.18); /* Enhanced tactile contrast */

  /* Primary Interactive CTA */
  --color-primary: #181d26;         /* Near-black primary action button */
  --color-primary-hover: #0d1218;
  --color-on-primary: #ffffff;
}
```

### 4.2 Dark Mode (Workbench / Low-Light Theme)

```css
[data-theme="dark"] {
  /* Canvas & Surfaces */
  --color-canvas: #0f1117;          /* Deep slate background */
  --color-surface-soft: #181d26;     /* Elevated panel surface */
  --color-surface-subtle: #1f242e;   /* Inner table container / header surface */
  --color-surface-hover: #262c38;    /* Interactive row hover */

  /* Ink & Typography */
  --color-ink: #f8fafc;             /* 16.4:1 ratio (AAA) - Primary text */
  --color-ink-muted: #cbd5e1;       /* 11.2:1 ratio (AAA) - Secondary copy */
  --color-ink-subtle: #94a3b8;      /* 6.34:1 ratio (AA) - Captions & metadata */
  --color-ink-disabled: #475569;

  /* Borders & Dividers */
  --color-hairline: #272d38;        /* Subtle slate hairline */
  --color-border-strong: #3b4252;   /* Distinct container boundary */
  --color-border-focus: #f8fafc;
  --color-focus-ring: rgba(248, 250, 252, 0.22);

  /* Primary Interactive CTA */
  --color-primary: #f8fafc;         /* High-contrast bright button in dark mode */
  --color-primary-hover: #e2e8f0;
  --color-on-primary: #0f1117;
}
```

---

## 5. Functional Ticket Status Palette

To prevent visual ambiguity under low light or distance, **"Esperando repuesto"** is placed in the **Violet/Purple** spectrum (260° hue), creating complete chromatic separation from the **Amber** (38° hue) of **"En diagnóstico"**:

### 5.1 Light Theme Status Palette

| Estado | Token Name | Text Color | Background Fill | Border Tint | Contrast on BG | Chromatic Intent |
|---|---|---|---|---|---|---|
| **Recibido** | `--status-received` | `#0369a1` (Sky 700) | `#f0f9ff` (Sky 50) | `#bae6fd` | 5.86:1 (AA) | Intake completed, pending triage |
| **En diagnóstico** | `--status-diagnostic`| `#b45309` (Amber 700) | `#fffbeb` (Amber 50) | `#fde68a` | 4.84:1 (AA) | Active technical bench inspection |
| **Esperando repuesto** | `--status-waiting-parts` | `#6d28d9` (Violet 700) | `#f5f3ff` (Violet 50) | `#ddd6fe` | **6.48:1 (AA)** | Blocked awaiting parts (Violet hue) |
| **Reparado** | `--status-repaired` | `#047857` (Emerald 700) | `#ecfdf5` (Emerald 50) | `#a7f3d0` | 5.02:1 (AA) | Work complete, verified, ready for pickup |
| **Entregado** | `--status-delivered` | `#475569` (Slate 600) | `#f8fafc` (Slate 50) | `#e2e8f0` | 5.72:1 (AA) | Closed / Archived ticket |

### 5.2 Dark Theme Status Palette

| Estado | Dark Text Color | Dark Background Fill | Dark Border Tint |
|---|---|---|---|
| **Recibido** | `#38bdf8` (Sky 400) | `rgba(2, 132, 199, 0.15)` | `rgba(56, 189, 248, 0.3)` |
| **En diagnóstico** | `#fbbf24` (Amber 400) | `rgba(217, 119, 6, 0.15)` | `rgba(251, 191, 36, 0.3)` |
| **Esperando repuesto** | `#a78bfa` (Violet 400) | `rgba(124, 58, 237, 0.15)` | `rgba(167, 139, 250, 0.3)` |
| **Reparado** | `#34d399` (Emerald 400) | `rgba(5, 150, 105, 0.15)` | `rgba(52, 211, 153, 0.3)` |
| **Entregado** | `#94a3b8` (Slate 400) | `rgba(71, 85, 105, 0.15)` | `rgba(148, 163, 184, 0.3)` |

### Component Token Implementation Example:

```css
/* Status Badge Primitives */
.badge-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: var(--radius-badge, 6px);
  border: 1px solid transparent;
  line-height: 1.2;
}

/* Light Theme Badges */
[data-theme="light"] .badge-status[data-status="recibido"],
:root:not([data-theme="dark"]) .badge-status[data-status="recibido"] {
  color: #0369a1;
  background-color: #f0f9ff;
  border-color: #bae6fd;
}

[data-theme="light"] .badge-status[data-status="en_diagnostico"],
:root:not([data-theme="dark"]) .badge-status[data-status="en_diagnostico"] {
  color: #b45309;
  background-color: #fffbeb;
  border-color: #fde68a;
}

[data-theme="light"] .badge-status[data-status="esperando_repuesto"],
:root:not([data-theme="dark"]) .badge-status[data-status="esperando_repuesto"] {
  color: #6d28d9;
  background-color: #f5f3ff;
  border-color: #ddd6fe;
}

[data-theme="light"] .badge-status[data-status="reparado"],
:root:not([data-theme="dark"]) .badge-status[data-status="reparado"] {
  color: #047857;
  background-color: #ecfdf5;
  border-color: #a7f3d0;
}

[data-theme="light"] .badge-status[data-status="entregado"],
:root:not([data-theme="dark"]) .badge-status[data-status="entregado"] {
  color: #475569;
  background-color: #f8fafc;
  border-color: #e2e8f0;
}

/* Dark Theme Badges */
[data-theme="dark"] .badge-status[data-status="recibido"] {
  color: #38bdf8;
  background-color: rgba(2, 132, 199, 0.15);
  border-color: rgba(56, 189, 248, 0.3);
}

[data-theme="dark"] .badge-status[data-status="en_diagnostico"] {
  color: #fbbf24;
  background-color: rgba(217, 119, 6, 0.15);
  border-color: rgba(251, 191, 36, 0.3);
}

[data-theme="dark"] .badge-status[data-status="esperando_repuesto"] {
  color: #a78bfa;
  background-color: rgba(124, 58, 237, 0.15);
  border-color: rgba(167, 139, 250, 0.3);
}

[data-theme="dark"] .badge-status[data-status="reparado"] {
  color: #34d399;
  background-color: rgba(5, 150, 105, 0.15);
  border-color: rgba(52, 211, 153, 0.3);
}

[data-theme="dark"] .badge-status[data-status="entregado"] {
  color: #94a3b8;
  background-color: rgba(71, 85, 105, 0.15);
  border-color: rgba(148, 163, 184, 0.3);
}
```

---

## 6. Layout, Tables & Forms Guidance

### 6.1 Tables & Data Grids
- **Row Heights:** 40px–44px for standard density.
- **Header:** Sticky top header with subtle surface background (`var(--color-surface-soft)`), uppercase/medium weight 12px text (`var(--color-ink-muted)`), and bottom border `var(--color-hairline)`.
- **Row Alternation / Hover:** Base row with smooth transition to `var(--color-surface-hover)` on hover.
- **Alignment:** Left-aligned for text/device descriptions; Right-aligned with tabular figures for prices, currency, and quantities; Centered for status badges.

### 6.2 Forms & Control Inputs
- **Inputs:** 36px–40px height, 6px border radius, 1px solid `var(--color-hairline)`, 14px font size.
- **Focus State:** 1px solid `var(--color-border-focus)` accompanied by `--focus-ring` (`0 0 0 3px var(--color-focus-ring)`).
- **Labels:** Positioned strictly above the field, 12px–13px, weight 500, color `var(--color-ink-muted)`. Helper text and captions placed beneath in `var(--color-ink-subtle)` (7.56:1 contrast ratio).

### 6.3 Dashboards & Summary Cards
- **Panels:** Surface `var(--color-canvas)`, 1px `var(--color-hairline)` border, 8px border radius, 16px–20px internal padding.
- **KPI Metrics:** 24px–28px font size for primary metric with small tabular caption beneath.
