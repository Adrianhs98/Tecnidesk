import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate


from sqlalchemy import func


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
