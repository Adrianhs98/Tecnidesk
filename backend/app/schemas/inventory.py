import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class InventoryCreate(BaseModel):
    item_name: str = Field(..., min_length=2, max_length=300)
    stock_quantity: int = Field(..., ge=0)
    cost_price: Decimal = Field(..., ge=0)
    selling_price: Decimal = Field(..., ge=0)
    low_stock_alert: int = Field(default=3, ge=0)


class InventoryUpdate(BaseModel):
    item_name: str | None = Field(default=None, min_length=2, max_length=300)
    cost_price: Decimal | None = Field(default=None, ge=0)
    selling_price: Decimal | None = Field(default=None, ge=0)
    low_stock_alert: int | None = Field(default=None, ge=0)


class InventoryRestock(BaseModel):
    quantity: int = Field(..., gt=0)


class InventoryResponse(BaseModel):
    id: uuid.UUID
    item_name: str
    stock_quantity: int
    cost_price: Decimal
    selling_price: Decimal
    low_stock_alert: int
    is_active: bool
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
