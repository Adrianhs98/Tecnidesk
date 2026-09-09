from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.inventory import InventoryCreate, InventoryUpdate


def test_inventory_create_strips_whitespace():
    item = InventoryCreate(
        item_name="   Display Samsung A12   ",
        stock_quantity=5,
        cost_price=Decimal("15.00"),
        selling_price=Decimal("25.00"),
        low_stock_alert=2,
    )
    assert item.item_name == "Display Samsung A12"


def test_inventory_create_rejects_whitespace_only():
    with pytest.raises(ValidationError) as exc_info:
        InventoryCreate(
            item_name="   ",
            stock_quantity=5,
            cost_price=Decimal("15.00"),
            selling_price=Decimal("25.00"),
            low_stock_alert=2,
        )
    assert "item_name must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_inventory_create_rejects_single_non_whitespace_char():
    with pytest.raises(ValidationError) as exc_info:
        InventoryCreate(
            item_name=" a  ",
            stock_quantity=5,
            cost_price=Decimal("15.00"),
            selling_price=Decimal("25.00"),
            low_stock_alert=2,
        )
    assert "item_name must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_inventory_update_strips_whitespace():
    update = InventoryUpdate(
        item_name="   Batería iPhone 12   "
    )
    assert update.item_name == "Batería iPhone 12"


def test_inventory_update_rejects_whitespace_only():
    with pytest.raises(ValidationError) as exc_info:
        InventoryUpdate(
            item_name="     "
        )
    assert "item_name must contain at least 2 non-whitespace characters" in str(exc_info.value)


def test_inventory_update_allows_none():
    update = InventoryUpdate(
        item_name=None,
        selling_price=Decimal("30.00"),
    )
    assert update.item_name is None
    assert update.selling_price == Decimal("30.00")
