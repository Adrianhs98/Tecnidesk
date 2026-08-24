# Implementation Tasks

## PR 1: Data & Schema Foundation
- [ ] Update `TechnicianResponse` and `TechnicianWithMetrics` Pydantic schemas to include `user_id: Optional[UUID] = None` (or int).
- [ ] Verify/update the `technicians` database model to ensure `user_id` correctly maps as a foreign key to `users` (create a migration if missing).
- [ ] Modify the `POST /technicians` endpoint logic and request body to accept optional fields: `{ "email": "string", "generate_access": boolean }`.
- [ ] Implement transaction logic in `POST /technicians` to conditionally create a user (role: technician), link the `user_id`, and send credentials via Resend (with rollback on email failure).

## PR 2: Endpoint & Frontend
- [ ] Create the new `POST /technicians/{id}/access` endpoint.
- [ ] Implement logic in `POST /technicians/{id}/access` to validate that the email doesn't exist (return `409 Conflict`), generate a secure password, create a user record, link the `user_id`, and send credentials via Resend.
- [ ] Ensure `POST /technicians/{id}/access` is wrapped in an atomic database transaction that rolls back if the Resend email dispatch fails (returning `502` or `400`).
- [ ] Update `TechniciansModal.jsx` (or equivalent view) to conditionally render a "Generar acceso" button if `tech.user_id` is null/undefined and `tech.is_active` is true.
- [ ] Create an Access Generation Dialog in the frontend to collect the technician's email when the "Generar acceso" button is clicked.
- [ ] Update the Technician Creation Form in the frontend to include a "Grant system access" toggle that shows a required email input when checked.
- [ ] Implement API calls and state management in the frontend to handle success (refetch/update state) and errors (`409` as "El correo ya está en uso", `502/400` as "Fallo al enviar correo, acceso no generado").

## Review Workload Forecast
- **Chained PRs recommended:** Yes
- **400-line budget risk:** Low/Moderate risk (Splitting into two PRs ensures each remains well within a 400-line budget)
