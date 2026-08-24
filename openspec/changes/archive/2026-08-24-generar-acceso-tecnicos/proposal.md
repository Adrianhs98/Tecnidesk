# SDD Proposal: Generar Acceso para Técnicos

## Business Problem
Administrators currently lack a streamlined way to grant system access (create a user account) for "ghost" technicians—technicians who exist in the system as records but do not have login credentials. Additionally, there is a need to create new technicians and grant them access simultaneously.

## Target Users
- **Administrators:** Who manage technicians and grant system access.
- **Technicians:** Who receive access and log into the system to perform their tasks.

## Product Outcome
- Administrators can seamlessly generate system access for existing ghost technicians via the TechniciansModal in the frontend.
- Administrators can create new technicians and optionally grant them system access at the same time.
- Technicians receive an automated email containing their generated credentials.

## Business Rules
- **Identification:** The frontend determines if a technician is a "ghost" based on the absence of a user_id in the TechnicianResponse (and related metrics).
- **Email Generation & Password:** 
  - The admin provides only the technician's email address.
  - The backend automatically generates a secure, temporary password.
  - Credentials are sent to the technician via the Resend email service.
- **State Restrictions:** The "Generar acceso" action must be disabled in the frontend for inactive technicians.
- **Revocation:** No dedicated revocation state or field is required; deactivating a technician normally is sufficient to block their system access.

## Edge Cases
- **Email Delivery Failure:** If the Resend email service fails to deliver the generated credentials (e.g., service downtime, invalid format), the entire user creation transaction must be rolled back. The backend must return an error (e.g., 502 Bad Gateway or 400 Bad Request) so the admin knows the action failed and the technician is not left in an inaccessible state.
- **Email Collision:** If the provided email address already exists in the users table, the backend must return a 409 Conflict error. Automatic merging of accounts is strictly prohibited.

## Non-goals
- Forcing a password change upon the technician's first login is out of scope (YAGNI).
- Automatically resolving email collisions or merging user accounts.

