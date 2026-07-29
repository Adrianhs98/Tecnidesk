import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, subscription_guard
from app.models.user import User
from app.schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventoryRestock,
    InventoryUpdate,
)
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


from app.schemas.pagination import PaginatedResponse
from fastapi import Query

@router.get("", response_model=PaginatedResponse[InventoryResponse])
async def list_inventory(
    search: str | None = None,
    sku: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Listar inventario del taller."""
    items, total = await inventory_service.list_inventory(db, current_user.shop_id, search, False, skip, limit, sku)
    return PaginatedResponse(items=items, total=total)


@router.post("", response_model=InventoryResponse)
async def create_inventory_item(
    data: InventoryCreate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Crear pieza nueva."""
    return await inventory_service.create_inventory_item(db, current_user.shop_id, data)


@router.patch("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: uuid.UUID,
    data: InventoryUpdate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Editar pieza."""
    return await inventory_service.update_inventory_item(db, current_user.shop_id, item_id, data)


@router.post("/{item_id}/restock", response_model=InventoryResponse)
async def restock_inventory_item(
    item_id: uuid.UUID,
    data: InventoryRestock,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Reabastecer stock."""
    return await inventory_service.restock_inventory_item(db, current_user.shop_id, item_id, data.quantity)


@router.delete("/{item_id}", status_code=204)
async def delete_inventory_item(
    item_id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete pieza (is_active = False)."""
    await inventory_service.delete_inventory_item(db, current_user.shop_id, item_id)
