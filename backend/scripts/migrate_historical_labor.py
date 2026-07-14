"""
Script de migración de datos para tickets históricos: Fase 2.3
Preserva los presupuestos de tickets antiguos (total_cost > 0 sin items)
creando un TicketItem de tipo labor, evitando que el nuevo cálculo SUM(items)
los regrese a $0.00.

Uso:
  python scripts/migrate_historical_labor.py
"""
import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.ticket import Ticket
from app.models.ticket_item import TicketItem, ItemTypeEnum


async def run_migration():
    async with AsyncSessionLocal() as session:
        # Obtener todos los tickets con total_cost > 0 cargando sus items
        stmt = select(Ticket).where(Ticket.total_cost > 0).options(selectinload(Ticket.items))
        result = await session.execute(stmt)
        tickets = result.scalars().all()
        
        migrated_count = 0
        for ticket in tickets:
            # Calcular la suma de los items existentes
            sum_items = sum([item.quantity * item.unit_price for item in ticket.items])
            labor_gap = ticket.total_cost - sum_items
            
            if labor_gap > 0:
                print(f"Ticket {ticket.id} - total_cost: {ticket.total_cost}, sum_items: {sum_items}. Creando labor_gap: {labor_gap}")
                
                new_item = TicketItem(
                    ticket_id=ticket.id,
                    item_type=ItemTypeEnum.labor,
                    description="Mano de obra y repuestos (migrado)",
                    quantity=1,
                    unit_price=labor_gap,
                    inventory_id=None
                )
                session.add(new_item)
                migrated_count += 1
                
        if migrated_count > 0:
            await session.commit()
            print(f"Migración completada. Se añadieron {migrated_count} items tipo labor.")
        else:
            print("No se requirieron migraciones. Todos los tickets están consistentes.")


if __name__ == "__main__":
    asyncio.run(run_migration())
