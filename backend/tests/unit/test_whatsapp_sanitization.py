from app.api.v1.endpoints.tracking import _sanitize_phone

def test_sanitize_phone_with_formatting():
    assert _sanitize_phone("+593 99 123-4567") == "593991234567"
    assert _sanitize_phone("(593) 991234567") == "593991234567"
    assert _sanitize_phone("593-99-123-4567") == "593991234567"

def test_sanitize_phone_empty_or_none():
    assert _sanitize_phone(None) is None
    assert _sanitize_phone("") is None
    assert _sanitize_phone("---") is None
