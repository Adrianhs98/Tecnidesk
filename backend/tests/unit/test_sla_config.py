"""
Unit tests for SLA configuration, schema validation, merging fallback logic,
and dynamic breach evaluation.
"""
import datetime
import uuid
import pytest
from pydantic import ValidationError

from app.models.ticket import Ticket, TicketStatusEnum
from app.schemas.shop import SlaConfigUpdate, SlaConfigResponse
from app.services.shop_service import (
    DEFAULT_SLA_THRESHOLDS_HOURS,
    get_effective_sla_thresholds,
)
from app.services.ticket_service import (
    is_ticket_sla_breached,
    SLA_THRESHOLDS_HOURS,
)


def test_default_sla_thresholds_constants():
    """Ensure system SLA constants match specifications."""
    assert DEFAULT_SLA_THRESHOLDS_HOURS["EN_ESPERA_INGRESO"] == 48
    assert DEFAULT_SLA_THRESHOLDS_HOURS["EN_REVISION"] == 24
    assert DEFAULT_SLA_THRESHOLDS_HOURS["EN_REPARACION"] == 48


def test_get_effective_sla_thresholds_defaults():
    """When custom_thresholds is None or empty, returns complete default dictionary."""
    assert get_effective_sla_thresholds(None) == DEFAULT_SLA_THRESHOLDS_HOURS
    assert get_effective_sla_thresholds({}) == DEFAULT_SLA_THRESHOLDS_HOURS


def test_get_effective_sla_thresholds_partial_override():
    """Partial override updates only specified status while retaining defaults for others."""
    custom = {"EN_REVISION": 12}
    effective = get_effective_sla_thresholds(custom)
    assert effective["EN_REVISION"] == 12
    assert effective["EN_ESPERA_INGRESO"] == 48
    assert effective["EN_REPARACION"] == 48


def test_get_effective_sla_thresholds_full_override():
    """Complete custom map overrides all configurable statuses."""
    custom = {
        "EN_ESPERA_INGRESO": 72,
        "EN_REVISION": 6,
        "EN_REPARACION": 96,
    }
    effective = get_effective_sla_thresholds(custom)
    assert effective == custom


def test_get_effective_sla_thresholds_ignores_invalid_keys_and_types():
    """Unknown statuses or out-of-boundary values are safely ignored in fallback merger."""
    custom = {
        "UNKNOWN_STATUS": 20,
        "EN_REVISION": 15,
        "EN_REPARACION": 1000,  # > 720, ignored
        "EN_ESPERA_INGRESO": -5,  # < 1, ignored
    }
    effective = get_effective_sla_thresholds(custom)
    assert effective["EN_REVISION"] == 15
    assert effective["EN_ESPERA_INGRESO"] == 48  # preserved default
    assert effective["EN_REPARACION"] == 48     # preserved default
    assert "UNKNOWN_STATUS" not in effective


def test_sla_config_update_schema_validation_valid():
    """SlaConfigUpdate accepts valid hour ranges (1 to 720)."""
    valid_payload = {
        "custom_thresholds": {
            "EN_ESPERA_INGRESO": 1,
            "EN_REVISION": 720,
            "EN_REPARACION": 36,
        }
    }
    schema = SlaConfigUpdate(**valid_payload)
    assert schema.custom_thresholds["EN_REVISION"] == 720


def test_sla_config_update_schema_validation_invalid_status():
    """SlaConfigUpdate rejects unconfigurable or invalid statuses."""
    invalid_payload = {
        "custom_thresholds": {
            "ESPERANDO_APROBACION": 24,
        }
    }
    with pytest.raises(ValidationError) as exc:
        SlaConfigUpdate(**invalid_payload)
    assert "no es configurable para SLA" in str(exc.value)


@pytest.mark.parametrize("invalid_hours", [0, -10, 721, 1000, 12.5, True, False])
def test_sla_config_update_schema_validation_invalid_hours(invalid_hours):
    """SlaConfigUpdate rejects out-of-boundary hours or non-integers."""
    invalid_payload = {
        "custom_thresholds": {
            "EN_REVISION": invalid_hours,
        }
    }
    with pytest.raises(ValidationError):
        SlaConfigUpdate(**invalid_payload)


def test_sla_config_response_schema():
    """SlaConfigResponse schema validates dictionary structures."""
    data = {
        "effective_thresholds": {"EN_REVISION": 12, "EN_ESPERA_INGRESO": 48, "EN_REPARACION": 48},
        "custom_thresholds": {"EN_REVISION": 12},
        "default_thresholds": DEFAULT_SLA_THRESHOLDS_HOURS,
    }
    resp = SlaConfigResponse(**data)
    assert resp.effective_thresholds["EN_REVISION"] == 12
    assert resp.custom_thresholds["EN_REVISION"] == 12
    assert resp.default_thresholds["EN_REVISION"] == 24


def test_is_ticket_sla_breached_with_defaults():
    """is_ticket_sla_breached calculates breach using system default thresholds."""
    now = datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.timezone.utc)

    # 10 hours ago -> not breached for EN_REVISION (24h)
    ticket_ok = Ticket(
        status=TicketStatusEnum.EN_REVISION,
        created_at=now - datetime.timedelta(hours=10),
    )
    assert is_ticket_sla_breached(ticket_ok, now=now) is False

    # 25 hours ago -> breached for EN_REVISION (24h)
    ticket_breached = Ticket(
        status=TicketStatusEnum.EN_REVISION,
        created_at=now - datetime.timedelta(hours=25),
    )
    assert is_ticket_sla_breached(ticket_breached, now=now) is True


def test_is_ticket_sla_breached_with_custom_thresholds():
    """is_ticket_sla_breached respects workshop-specific custom overrides."""
    now = datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.timezone.utc)
    custom = {"EN_REVISION": 12}

    # 15 hours ago in EN_REVISION:
    # Default is 24h (not breached), but custom is 12h (breached!)
    ticket = Ticket(
        status=TicketStatusEnum.EN_REVISION,
        created_at=now - datetime.timedelta(hours=15),
    )
    assert is_ticket_sla_breached(ticket, now=now) is False  # with defaults
    assert is_ticket_sla_breached(ticket, now=now, custom_thresholds=custom) is True  # with custom override


def test_is_ticket_sla_breached_paused_and_terminal_statuses():
    """Paused and terminal statuses always return False regardless of elapsed time."""
    now = datetime.datetime(2026, 8, 22, 12, 0, tzinfo=datetime.timezone.utc)
    way_past = now - datetime.timedelta(days=10)

    for st in [
        TicketStatusEnum.ESPERANDO_APROBACION,
        TicketStatusEnum.ESPERANDO_REPUESTO,
        TicketStatusEnum.LISTO_PARA_RETIRAR,
        TicketStatusEnum.NO_APROBADO,
    ]:
        ticket = Ticket(status=st, created_at=way_past)
        assert is_ticket_sla_breached(ticket, now=now) is False
