# Design: Centralized Currency Formatting Utility

## 1. Context
Multiple frontend components parse and format monetary values manually using ad-hoc `parseFloat(val).toFixed(2)` expressions. This creates code duplication, inconsistent null/NaN handling, and maintenance friction.

## 2. Proposed Architecture

### 2.1 Core Utility Module (`frontend/src/utils/currency.js`)
Create a single, pure utility function:
```javascript
export function formatCurrency(amount, options = {}) {
  const { fallback = "$0.00", showSymbol = true } = options;
  if (amount === null || amount === undefined || amount === "") {
    return fallback;
  }
  const numeric = typeof amount === "number" ? amount : parseFloat(amount);
  if (Number.isNaN(numeric)) {
    return fallback;
  }
  const formatted = numeric.toFixed(2);
  return showSymbol ? `$${formatted}` : formatted;
}
```

### 2.2 Decisions & Trade-offs

#### Decision: Standalone Pure Function vs. `Intl.NumberFormat`
- **Option A (Chosen)**: Lightweight `parseFloat` + `.toFixed(2)` wrapper matching current app style and Ecuador's USD standard (`$X.XX`).
  - *Pros*: Zero bundle overhead, predictable output across all browsers/node environments, simple unit test assertions.
  - *Cons*: Doesn't automatically adapt to non-USD locales (not needed for this SaaS).
- **Option B**: `Intl.NumberFormat("es-EC", { style: "currency", currency: "USD" })`.
  - *Pros*: Native localization.
  - *Cons*: Browser differences with non-breaking spaces (e.g. `$\u00a012.00` vs `$12.00`) which complicate string matching and UI alignment.

#### Decision: Location
- Place under `frontend/src/utils/currency.js` alongside `date.js` and `privacy.js` to preserve existing project structure.

## 3. File Changes

### New Files
- `frontend/src/utils/currency.js` — The core formatter function.
- `frontend/src/tests/utils/currency.test.ts` — Comprehensive test suite for all scenarios.

### Modified Files (Adoption)
- `frontend/src/components/shared/ResultCard.jsx`
- `frontend/src/pages/TrackingPortal.jsx`
- `frontend/src/features/admin/components/AdminTicketCard.jsx`
- `frontend/src/features/admin/components/DiagnosticModal.jsx`
- `frontend/src/features/admin/components/InventoryModal.jsx`
- `frontend/src/features/admin/components/PartsSelector.jsx`
- `frontend/src/features/admin/components/TechniciansModal.jsx`

## 4. Verification Plan
- Run `vitest run` on `frontend/src/tests/utils/currency.test.ts` to confirm 100% scenario compliance.
- Run frontend build (`npm run build`) to ensure type and import safety across all updated components.
