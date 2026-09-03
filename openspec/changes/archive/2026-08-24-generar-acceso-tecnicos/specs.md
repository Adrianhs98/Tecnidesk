# SDD Specifications: Generar Acceso para Técnicos

## 1. Backend Changes

### 1.1 API Endpoints

- **`POST /technicians/{id}/access`**
  - **Description:** Generates system access for an existing technician.
  - **Request Body:** `{ "email": "string" }`
  - **Response:** `200 OK` on success, `409 Conflict` if email exists, `502 Bad Gateway` (or `400 Bad Request`) if Resend fails.
  - **Logic:**
    - Validate email doesn't exist in `users`.
    - Generate a secure temporary password.
    - Start a DB transaction.
    - Create a user record (role: technician).
    - Update `technicians.user_id`.
    - Attempt to send credentials email via Resend.
    - Rollback transaction if Resend throws an error. Commit otherwise.

- **`POST /technicians`** (Modification)
  - **Description:** Allow optional access generation upon technician creation.
  - **Request Body Modification:** Add optional fields `{ "email": "string", "generate_access": true/false }`
  - **Logic:** Similar to above, wrapped in a transaction along with technician creation.

### 1.2 Data Schemas (Pydantic / DB)

- **`TechnicianResponse`** / **`TechnicianWithMetrics`**:
  - Add `user_id: Optional[UUID] = None` (or int, depending on system UUID).
- Ensure `technicians` table has `user_id` as a foreign key to `users` (already exists or add migration if missing).

## 2. Frontend Changes

### 2.1 UI Components

- **`TechniciansModal.jsx` (or equivalent Technician Details/List view)**
  - Conditionally render a "Generar acceso" button.
  - **Conditions:** Render if `tech.user_id` is null/undefined AND `tech.is_active === true`.
  - Disable or hide if inactive.
  
- **Access Generation Dialog**
  - A modal/prompt when "Generar acceso" is clicked to collect the technician's email address.
  
- **Technician Creation Form**
  - Add a toggle/checkbox: "Grant system access".
  - If checked, show a required input field for Email.

### 2.2 State Management & API Calls

- Implement API call functions for the new endpoints.
- Handle specific error codes:
  - `409`: Show toast/alert "El correo ya está en uso".
  - `502/400`: Show toast/alert "Fallo al enviar correo, acceso no generado".
- Update local state (refetch technicians or manually update `user_id` in the local list) upon successful access generation.
