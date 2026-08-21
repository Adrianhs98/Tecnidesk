import asyncio
import datetime
import os
from sqlalchemy import select, func, not_
from app.database import AsyncSessionLocal
from app.models.ticket import Ticket, TicketStatusEnum

async def run_baseline():
    async with AsyncSessionLocal() as session:
        # Define active statuses condition
        active_statuses = [TicketStatusEnum.LISTO_PARA_RETIRAR, TicketStatusEnum.NO_APROBADO]
        
        # Base query for active tickets
        base_query = select(Ticket).where(not_(Ticket.status.in_(active_statuses)))
        
        # Total active tickets
        total_active_query = select(func.count()).select_from(base_query.subquery())
        total_active_result = await session.execute(total_active_query)
        total_active = total_active_result.scalar() or 0
        
        # Active without technician
        no_tech_query = select(func.count()).select_from(
            base_query.where(Ticket.technician_id.is_(None)).subquery()
        )
        no_tech_result = await session.execute(no_tech_query)
        no_tech = no_tech_result.scalar() or 0
        
        # Active older than 72 hours
        seventy_two_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=72)
        old_query = select(func.count()).select_from(
            base_query.where(Ticket.created_at < seventy_two_hours_ago).subquery()
        )
        old_result = await session.execute(old_query)
        old = old_result.scalar() or 0

        markdown_content = f"""# Telemetry Baseline

- **Total Active Tickets**: {total_active}
- **Active Tickets without Technician**: {no_tech}
- **Active Tickets > 72h Old**: {old}
"""
        
        output_path = os.path.join(
            os.path.dirname(__file__), 
            '../../openspec/changes/2026-08-21-workbench-operativo-fase1/telemetry_baseline.md'
        )
        output_path = os.path.abspath(output_path)
        
        # ensure dir exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Metrics saved to {output_path}")
        print(f"Total: {total_active}, No Tech: {no_tech}, >72h: {old}")

if __name__ == "__main__":
    asyncio.run(run_baseline())
