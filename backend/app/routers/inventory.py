import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, subscription_guard
from app.models.user import User
from app.models.inventory import Inventory
from app.schemas.inventory import (
    InventoryCreate,
    InventoryResponse,
    InventoryRestock,
    InventoryUpdate,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/inventory", tags=["inventory"])

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
    stmt = select(Inventory).where(Inventory.shop_id == current_user.shop_id)
    stmt = stmt.where(Inventory.is_active == True)
        
    if search:
        stmt = stmt.where(Inventory.item_name.ilike(f"%{search}%"))
        
    if sku and hasattr(Inventory, 'sku'):
        stmt = stmt.where(Inventory.sku.ilike(f"%{sku}%"))
            
    total_query = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one_or_none() or 0
        
    stmt = stmt.order_by(Inventory.item_name).offset(skip).limit(limit)
    result = await db.execute(stmt)
    items = list(result.scalars().all())
    return PaginatedResponse(items=items, total=total)


@router.post("", response_model=InventoryResponse)
async def create_inventory_item(
    data: InventoryCreate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Crear pieza nueva."""
    item = Inventory(
        shop_id=current_user.shop_id,
        item_name=data.item_name,
        stock_quantity=data.stock_quantity,
        cost_price=data.cost_price,
        selling_price=data.selling_price,
        low_stock_alert=data.low_stock_alert,
        is_active=True,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: uuid.UUID,
    data: InventoryUpdate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Editar pieza."""
    stmt = select(Inventory).where(Inventory.id == item_id, Inventory.shop_id == current_user.shop_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
        
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{item_id}/restock", response_model=InventoryResponse)
async def restock_inventory_item(
    item_id: uuid.UUID,
    data: InventoryRestock,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Reabastecer stock."""
    stmt = select(Inventory).where(Inventory.id == item_id, Inventory.shop_id == current_user.shop_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
    item.stock_quantity += data.quantity
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_inventory_item(
    item_id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete pieza (is_active = False)."""
    stmt = select(Inventory).where(Inventory.id == item_id, Inventory.shop_id == current_user.shop_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
    item.is_active = False
    await db.commit()
