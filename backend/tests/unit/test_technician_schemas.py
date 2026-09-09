import pytest
from pydantic import ValidationError
from app.schemas.technician import TechnicianCreate, TechnicianUpdate


def test_technician_create_strips_full_name():
    tech = TechnicianCreate(
        full_name="   Carlos Mendez   ",
        contact="0991234567",
        declared_specialty="Microsoldadura",
    )
    assert tech.full_name == "Carlos Mendez"


def test_technician_create_rejects_whitespace_only_full_name():
    with pytest.raises(ValidationError) as exc_info:
        TechnicianCreate(
            full_name="    ",
            contact="0991234567",
        )
    assert "full_name must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_technician_create_rejects_single_non_whitespace_char():
    with pytest.raises(ValidationError) as exc_info:
        TechnicianCreate(
            full_name=" c ",
            contact="0991234567",
        )
    assert "full_name must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_technician_create_normalizes_empty_optional_fields():
    tech = TechnicianCreate(
        full_name="Juan Perez",
        contact="   ",
        declared_specialty="   ",
    )
    assert tech.contact is None
    assert tech.declared_specialty is None


def test_technician_create_strips_valid_optional_fields():
    tech = TechnicianCreate(
        full_name="Juan Perez",
        contact="  0991234567  ",
        declared_specialty="  Pantallas  ",
    )
    assert tech.contact == "0991234567"
    assert tech.declared_specialty == "Pantallas"


def test_technician_update_strips_full_name():
    update = TechnicianUpdate(
        full_name="   Carlos M.   "
    )
    assert update.full_name == "Carlos M."


def test_technician_update_rejects_whitespace_only():
    with pytest.raises(ValidationError) as exc_info:
        TechnicianUpdate(
            full_name="   "
        )
    assert "full_name must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_technician_update_allows_none():
    update = TechnicianUpdate(
        full_name=None,
        contact="0991234567",
    )
    assert update.full_name is None
    assert update.contact == "0991234567"


def test_technician_update_normalizes_empty_optional_fields():
    update = TechnicianUpdate(
        contact="   ",
        declared_specialty="   ",
    )
    assert update.contact is None
    assert update.declared_specialty is None
