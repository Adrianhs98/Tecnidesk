# Tasks: Contact WhatsApp Validation

## 1. Unit Tests
- [ ] Create (or update) `backend/tests/unit/test_auth_schemas.py`
- [ ] Add test for a valid 12-digit number ("593991234567")
- [ ] Add test failing when number contains `+`
- [ ] Add test failing when number contains spaces or letters

## 2. Implementation
- [ ] Open `backend/app/schemas/auth.py`
- [ ] Update `RegisterRequest.contact_whatsapp` to include `pattern=r"^\d+$"`
- [ ] Run tests to verify the tests now pass

## 3. Verification
- [ ] Run `pytest backend/tests/unit/test_auth_schemas.py`
- [ ] Mark verification complete
