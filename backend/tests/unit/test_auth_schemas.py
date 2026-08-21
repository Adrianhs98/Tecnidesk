from pydantic import ValidationError
import pytest
from app.schemas.auth import RegisterRequest

def test_register_request_whatsapp_valid():
    request = RegisterRequest(
        email="test@shop.com",
        shop_name="My Shop",
        contact_whatsapp="593991234567"
    )
    assert request.contact_whatsapp == "593991234567"

def test_register_request_whatsapp_no_plus():
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(
            email="test@shop.com",
            shop_name="My Shop",
            contact_whatsapp="+593991234567"
        )
    assert "String should match pattern" in str(exc_info.value)

def test_register_request_whatsapp_no_spaces_or_letters():
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="test@shop.com",
            shop_name="My Shop",
            contact_whatsapp="593 99 123"
        )
        
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="test@shop.com",
            shop_name="My Shop",
            contact_whatsapp="593abc12345"
        )
