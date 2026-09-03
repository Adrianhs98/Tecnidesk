from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.customer import Customer
from app.schemas.pagination import PaginatedResponse
from app.schemas.client import ClientResponse

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=PaginatedResponse[ClientResponse])
async def get_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Customer).where(Customer.shop_id == current_user.shop_id)

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
    total_result = await db.execute(total_query)
    total = total_result.scalar_one_or_none() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return PaginatedResponse(items=items, total=total)
