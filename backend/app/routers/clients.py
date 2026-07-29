from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.client_service import ClientService
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
    service = ClientService(db)
    items, total = await service.get_clients(current_user.shop_id, skip, limit, search)
    return PaginatedResponse(items=items, total=total)
