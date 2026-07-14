import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, subscription_guard
from app.models.shop import Shop
from app.schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventoryRestock,
    InventoryUpdate,
)
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=list[InventoryResponse])
async def list_inventory(
    search: str | None = None,
    current_shop: Shop = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Listar inventario del taller."""
    return await inventory_service.list_inventory(db, current_shop.id, search)


@router.post("", response_model=InventoryResponse)
async def create_inventory_item(
    data: InventoryCreate,
    current_shop: Shop = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Crear pieza nueva."""
    return await inventory_service.create_inventory_item(db, current_shop.id, data)


@router.patch("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: uuid.UUID,
    data: InventoryUpdate,
    current_shop: Shop = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Editar pieza."""
    return await inventory_service.update_inventory_item(db, current_shop.id, item_id, data)


@router.post("/{item_id}/restock", response_model=InventoryResponse)
async def restock_inventory_item(
    item_id: uuid.UUID,
    data: InventoryRestock,
    current_shop: Shop = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Reabastecer stock."""
    return await inventory_service.restock_inventory_item(db, current_shop.id, item_id, data.quantity)


@router.delete("/{item_id}", status_code=204)
async def delete_inventory_item(
    item_id: uuid.UUID,
    current_shop: Shop = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete pieza (is_active = False)."""
    await inventory_service.delete_inventory_item(db, current_shop.id, item_id)
