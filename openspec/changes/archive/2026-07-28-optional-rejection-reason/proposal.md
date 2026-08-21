# Proposal: Optional Rejection Reason

## Why
When clients reject a ticket quote via the public tracking endpoint, they currently have no way to communicate *why* they rejected it (e.g., "Too expensive", "I bought a new phone instead"). Adding a reason provides valuable feedback to the shop technicians.

## What
Allow the public `/reject` endpoint to accept an optional `rejection_reason` from the client. To avoid a database schema migration and keep this change low-risk, the optional reason will be prepended to the ticket's `internal_notes` so the technician can see it immediately.

## Capabilities
- `optional-rejection-reason`: The tracking API `/reject` endpoint accepts an optional reason and persists it in the ticket's internal notes.
