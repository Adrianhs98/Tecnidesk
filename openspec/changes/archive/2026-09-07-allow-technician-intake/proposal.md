# Proposal: Allow Technician Device Intake (Per-Shop Flag)

## Problem Statement
Currently in TecniDesk, ticket intake is treated as an administrator-only capability in the UI, while the backend `POST /tickets` endpoint only checks for an active subscription without asserting user role permissions or shop policy. Many workshops operate with technicians who also serve at the counter or directly receive devices from customers. However, other workshops strictly segregate front-desk intake from bench repair.

A configurable, opt-in mechanism is required to allow shop owners to authorize technicians to intake devices while preserving strict multitenant security and least-privilege defaults.

## Proposed Solution
1. **Shop Policy Configuration**:
   - Add `allow_technician_intake: Mapped[bool]` to the `Shop` model with default `False` (`server_default="false"`).
   - Provide `GET /shops/settings` and `PATCH /shops/settings` endpoints in `shops.py` (protected by `admin_guard`) to read and toggle this setting.
2. **Backend Authorization Guard**:
   - Introduce `verify_can_create_ticket` dependency for `POST /tickets`:
     - Role `admin`: allowed unconditionally (under active subscription).
     - Role `technician`: allowed if and only if `shop.allow_technician_intake == True`.
     - Other roles or technicians in restricted shops: HTTP 403 Forbidden.
3. **Technician Profile Reflection**:
   - Expose `allow_technician_intake: bool` in `TechnicianMeResponse` (`GET /technicians/me`) so the client dashboard knows intake authorization without an extra network request.
4. **Frontend Integration**:
   - In Admin Settings: add a clean toggle in `SlaSettingsModal.jsx` (or shop settings UI) to toggle technician intake.
   - In Technician Dashboard: if `allow_technician_intake` is true, render an "Ingresar Equipo" action that opens `NewTicketModal`.
5. **Testing & Verification**:
   - Comprehensive unit and integration test coverage for guards, settings endpoints, profile schema, and frontend UI.
