import uuid
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.customer import Customer
from typing import Tuple, List

class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_clients(
        self,
        shop_id: uuid.UUID,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None
    ) -> Tuple[List[Customer], int]:
        query = select(Customer).where(Customer.shop_id == shop_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Customer.full_name.ilike(search_term),
                    Customer.email.ilike(search_term),
                    Customer.phone_number.ilike(search_term),
                )
            )

        total_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one_or_none() or 0

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total
