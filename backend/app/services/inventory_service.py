import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate


from sqlalchemy import func

async def list_inventory(
    session: AsyncSession, shop_id: uuid.UUID, search: str | None = None, include_inactive: bool = False, skip: int = 0, limit: int = 50, sku: str | None = None
) -> tuple[list[Inventory], int]:
    """Lista las piezas de inventario del taller."""
    stmt = select(Inventory).where(Inventory.shop_id == shop_id)
    
    if not include_inactive:
        stmt = stmt.where(Inventory.is_active == True)
        
    if search:
        stmt = stmt.where(Inventory.item_name.ilike(f"%{search}%"))
        
    if sku:
        if hasattr(Inventory, 'sku'):
            stmt = stmt.where(Inventory.sku.ilike(f"%{sku}%"))
            
    total_query = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(total_query)
    total = total_result.scalar_one_or_none() or 0
        
    stmt = stmt.order_by(Inventory.item_name).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all()), total


async def create_inventory_item(
    session: AsyncSession, shop_id: uuid.UUID, data: InventoryCreate
) -> Inventory:
    """Crea una nueva pieza de inventario."""
    item = Inventory(
        shop_id=shop_id,
        item_name=data.item_name,
        stock_quantity=data.stock_quantity,
        cost_price=data.cost_price,
        selling_price=data.selling_price,
        low_stock_alert=data.low_stock_alert,
        is_active=True,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_inventory_item(
    session: AsyncSession, shop_id: uuid.UUID, item_id: uuid.UUID, data: InventoryUpdate
) -> Inventory:
    """Edita nombre/precios/alerta de una pieza."""
    stmt = select(Inventory).where(Inventory.id == item_id, Inventory.shop_id == shop_id)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
        
    await session.commit()
    await session.refresh(item)
    return item


async def restock_inventory_item(
    session: AsyncSession, shop_id: uuid.UUID, item_id: uuid.UUID, quantity: int
) -> Inventory:
    """Suma stock (reabastecer)."""
    stmt = select(Inventory).where(Inventory.id == item_id, Inventory.shop_id == shop_id)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
    item.stock_quantity += quantity
    await session.commit()
    await session.refresh(item)
    return item


async def delete_inventory_item(
    session: AsyncSession, shop_id: uuid.UUID, item_id: uuid.UUID
) -> None:
    """Soft-delete de una pieza."""
    stmt = select(Inventory).where(Inventory.id == item_id, Inventory.shop_id == shop_id)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        
    item.is_active = False
    await session.commit()


async def deduct_stock(
    session: AsyncSession, inventory_id: uuid.UUID, quantity: int
) -> None:
    """Descuenta stock atómicamente."""
    result = await session.execute(
        update(Inventory)
        .where(Inventory.id == inventory_id)
        .where(Inventory.stock_quantity >= quantity)
        .values(stock_quantity=Inventory.stock_quantity - quantity)
    )
    if result.rowcount == 0:
        # Se verifica si es que no existe o si es que no hay stock
        item = await session.get(Inventory, inventory_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        raise HTTPException(status_code=409, detail=f"Stock insuficiente para '{item.item_name}'")


async def restore_stock(
    session: AsyncSession, inventory_id: uuid.UUID, quantity: int
) -> None:
    """Restaura stock atómicamente."""
    await session.execute(
        update(Inventory)
        .where(Inventory.id == inventory_id)
        .values(stock_quantity=Inventory.stock_quantity + quantity)
    )
