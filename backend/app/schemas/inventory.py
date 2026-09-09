import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryCreate(BaseModel):
    item_name: str = Field(..., min_length=2, max_length=300)
    stock_quantity: int = Field(..., ge=0)
    cost_price: Decimal = Field(..., ge=0)
    selling_price: Decimal = Field(..., ge=0)
    low_stock_alert: int = Field(default=3, ge=0)

    @field_validator("item_name")
    @classmethod
    def sanitize_item_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("item_name must contain at least 2 non-whitespace characters")
        return cleaned


class InventoryUpdate(BaseModel):
    item_name: str | None = Field(default=None, min_length=2, max_length=300)
    cost_price: Decimal | None = Field(default=None, ge=0)
    selling_price: Decimal | None = Field(default=None, ge=0)
    low_stock_alert: int | None = Field(default=None, ge=0)

    @field_validator("item_name")
    @classmethod
    def sanitize_item_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("item_name must contain at least 2 non-whitespace characters")
        return cleaned


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
