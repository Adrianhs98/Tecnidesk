# Proposal: Centralized Currency Formatting Utility

## 1. Intent
Create a robust, centralized utility for formatting currency (prices, costs) in the frontend.

## 2. Motivation
Currently, at least 7 components (`ResultCard.jsx`, `DiagnosticModal.jsx`, `AdminTicketCard.jsx`, `InventoryModal.jsx`, `PartsSelector.jsx`, `TechniciansModal.jsx`, `TrackingPortal.jsx`) manually parse and format prices using variations of `parseFloat(val).toFixed(2)` or `Number(val).toFixed(2)`. This approach:
- Is repetitive and scatters presentation logic across the component tree.
- Handles edge cases (null, undefined, invalid strings, NaN) inconsistently, occasionally rendering `$NaN`.
- Risks throwing `TypeError` if `.toFixed()` is called directly on an undefined object.

## 3. Impact
- **Risk**: Low. Pure utility addition with isolated, testable logic.
- **Affected Area**: Frontend (`src/utils/` and the 7 affected components).
- **Architecture**: Enforces the DRY principle and strictly separates data presentation logic from React UI components.

## 4. Capabilities
- **frontend-currency-formatting**: Reliable parsing and formatting of monetary values, safe handling of invalid/missing data, and configurable output.
