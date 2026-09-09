# Proposal: Technicians Modal Client-Side Validation

## Problem
In `frontend/src/features/admin/components/TechniciansModal.jsx`, technician creation and editing suffer from three UX and data integrity issues:
1. **Unsanitized Payload:** `formData.full_name` is sent without trimming. If an administrator inputs leading or trailing spaces (e.g. `"  Carlos Mendez  "`), they are sent directly to the API. If `full_name` has only whitespace, it bypasses basic checks.
2. **Ghost Whitespace in Optional Fields:** `formData.contact` and `formData.declared_specialty` use `formData.contact || null`. If the input contains whitespace (e.g. `"   "`), it is truthy and sent as a whitespace string rather than `null`.
3. **Disruptive Alert Error Handling:** On error, `handleSubmit` uses native browser `alert(err.message)` instead of an integrated, inline feedback banner (like `InventoryModal` or `RegisterPage`).

## Solution
1. Update `TechniciansModal.jsx`:
   - Add `formError` state to display inline validation/API error banners.
   - In `handleSubmit`, validate that `formData.full_name.trim().length >= 2`. Display inline error if invalid.
   - If `generate_access` is checked, validate that `formData.email.trim()` matches standard email format.
   - Normalize `contact` and `declared_specialty`: trim strings and convert empty/whitespace-only values to `null`.
   - Normalize `email` with `.trim().toLowerCase()`.
   - Replace `alert(err.message)` with `setFormError(err.message)`.
2. Add component test suite in `frontend/src/tests/components/TechniciansModal.test.jsx` covering:
   - Client-side validation blocking submit for whitespace-only or short full name.
   - Normalized payload dispatching trimmed `full_name` and `null` for empty/whitespace optional fields.
   - Inline error display upon submission failure.

## Capabilities
### New Capabilities
- `technician-client-validation`: Client-side input validation, string sanitization, and inline error feedback in the admin technicians modal.

## Impact
- **New Files:**
  - `frontend/src/tests/components/TechniciansModal.test.jsx`
- **Modified Files:**
  - `frontend/src/features/admin/components/TechniciansModal.jsx`
- **Dependencies:** None.
- **Breaking Changes:** None. Purely improves client-side validation and UX.
