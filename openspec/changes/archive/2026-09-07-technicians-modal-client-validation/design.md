# Design: Technicians Modal Client-Side Validation

## Architecture & Context
The technician management interface resides in `frontend/src/features/admin/components/TechniciansModal.jsx`. It supports listing metrics, adding new technicians, and editing existing ones. Adding client-side validation and inline error rendering standardizes the user experience with other modals (`NewTicketModal`, `InventoryModal`).

## Decisions & Tradeoffs
1. **Adding `formError` state:**
   - *Decision:* Declare `const [formError, setFormError] = useState(null);`.
   - *Why:* Keeps errors local to the active form view, resets when switching views or typing, and avoids disruptive window alerts.

2. **Sanitizing on submit vs onChange:**
   - *Decision:* Sanitize `full_name`, `contact`, and `declared_specialty` upon `handleSubmit` while checking `fullName.length < 2`.
   - *Why:* Ensures natural typing without cursor manipulation on mobile/desktop keyboards.

3. **Inline Error Banner Markup:**
   - *Decision:* Use `.admin-error-bar` matching the design system standard seen across the application.

## File Changes
- **`frontend/src/features/admin/components/TechniciansModal.jsx`**:
  - Add `formError` state and render error banner in `renderForm`.
  - Validate and trim `full_name`, `contact`, and `declared_specialty`.
  - Replace `alert(err.message)` with `setFormError(err.message)`.
- **`frontend/src/tests/components/TechniciansModal.test.jsx`**:
  - Unit tests asserting validation blocking, sanitized payloads, and error rendering.
