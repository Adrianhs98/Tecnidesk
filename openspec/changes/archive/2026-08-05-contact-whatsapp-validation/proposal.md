# Change Proposal: Contact WhatsApp Validation

## The Problem
Currently, the `RegisterRequest` schema in `backend/app/schemas/auth.py` validates `contact_whatsapp` only by length (10-20 characters). The description explicitly asks for "formato internacional sin '+'", but the API allows arbitrary characters (e.g. letters or symbols). This can lead to messaging failures down the line.

## The Solution
We will add a strict regex pattern validation to `contact_whatsapp` to ensure it only accepts numerical digits `0-9`.

## Capabilities
- Add regex validation to `RegisterRequest.contact_whatsapp` in `backend/app/schemas/auth.py`
- Add unit tests to verify the validation in `backend/tests/unit/test_auth_schemas.py`

## Out of Scope
- Modifying frontend validation (this is strictly a backend schema update).
- Modifying existing stored data.
