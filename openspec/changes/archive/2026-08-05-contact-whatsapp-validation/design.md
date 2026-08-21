# Design: Contact WhatsApp Validation

## Approach
We will add a regular expression pattern to the `Field` definition of `contact_whatsapp` in the `RegisterRequest` Pydantic model. 

## File Changes
1. **`backend/app/schemas/auth.py`**
   - Modify `RegisterRequest.contact_whatsapp` to include `pattern=r"^\d+$"`.
2. **`backend/tests/unit/test_auth_schemas.py`** (new or updated)
   - Add unit tests instantiating `RegisterRequest` with valid and invalid `contact_whatsapp` values to ensure the validation raises `ValidationError` as expected.

## Decisions
- **Regex `^\d+$`**: Chosen because it strictly enforces that every character from the start to the end of the string is a digit. It cleanly rejects `+`, spaces, dashes, or letters.
- **Why not sanitize the input instead?**: While `test_whatsapp_sanitization.py` exists for tracking tokens, shop registration should enforce strict format upfront so the user corrects it immediately, rather than silently altering a primary communication channel which could result in a malformed number if the sanitization strips out critical details unintentionally.
