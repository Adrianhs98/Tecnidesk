# Tasks: Sanitize WhatsApp Number

- [x] **Task 1: Add phone sanitization helper in tracking.py**
  - Implement `_sanitize_phone` function using regex `re.sub(r"\D", "", phone)`.
- [x] **Task 2: Apply sanitization in _enrich_response**
  - Wrap `contact_whatsapp` value in `_enrich_response` with `_sanitize_phone`.
- [x] **Task 3: Add unit test for WhatsApp number sanitization**
  - Add test in `backend/tests/unit/test_whatsapp_sanitization.py` verifying formatting characters are removed.
