import pytest
from pydantic import ValidationError
from app.schemas.ticket import TicketCreate


def test_ticket_create_strips_brand_and_model():
    ticket = TicketCreate(
        client_email="client@test.com",
        device_brand="   Apple   ",
        device_model="   iPhone 13 Pro   ",
        issue_description="Pantalla rota y no enciende",
    )
    assert ticket.device_brand == "Apple"
    assert ticket.device_model == "iPhone 13 Pro"


def test_ticket_create_rejects_whitespace_only_brand():
    with pytest.raises(ValidationError) as exc_info:
        TicketCreate(
            client_email="client@test.com",
            device_brand="    ",
            device_model="iPhone 13",
            issue_description="Pantalla rota y no enciende",
        )
    assert "device_brand must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_ticket_create_rejects_whitespace_only_model():
    with pytest.raises(ValidationError) as exc_info:
        TicketCreate(
            client_email="client@test.com",
            device_brand="Apple",
            device_model="    ",
            issue_description="Pantalla rota y no enciende",
        )
    assert "device_model must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_ticket_create_rejects_short_brand():
    with pytest.raises(ValidationError) as exc_info:
        TicketCreate(
            client_email="client@test.com",
            device_brand=" A ",
            device_model="iPhone 13",
            issue_description="Pantalla rota y no enciende",
        )
    assert "device_brand must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_ticket_create_strips_issue_description():
    ticket = TicketCreate(
        client_email="client@test.com",
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="   Pantalla rota y no enciende tras caída   ",
    )
    assert ticket.issue_description == "Pantalla rota y no enciende tras caída"


def test_ticket_create_rejects_whitespace_only_issue_description():
    with pytest.raises(ValidationError) as exc_info:
        TicketCreate(
            client_email="client@test.com",
            device_brand="Apple",
            device_model="iPhone 13",
            issue_description="         ",
        )
    assert "issue_description must contain at least 5 non-whitespace characters" in str(exc_info.value)


def test_ticket_create_rejects_short_issue_description():
    with pytest.raises(ValidationError) as exc_info:
        TicketCreate(
            client_email="client@test.com",
            device_brand="Apple",
            device_model="iPhone 13",
            issue_description=" mal ",
        )
    assert "issue_description must contain at least 5 non-whitespace characters" in str(exc_info.value)


def test_ticket_create_normalizes_empty_optional_fields():
    ticket = TicketCreate(
        client_email="client@test.com",
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Pantalla rota y no enciende",
        client_name="    ",
        client_phone="   ",
        internal_notes="   ",
    )
    assert ticket.client_name is None
    assert ticket.client_phone is None
    assert ticket.internal_notes is None


def test_ticket_create_preserves_valid_optional_fields():
    ticket = TicketCreate(
        client_email="client@test.com",
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Pantalla rota y no enciende",
        client_name="   Juan Perez   ",
        client_phone="  0991234567  ",
        internal_notes="  Equipo con golpes en chasis  ",
    )
    assert ticket.client_name == "Juan Perez"
    assert ticket.client_phone == "0991234567"
    assert ticket.internal_notes == "Equipo con golpes en chasis"
