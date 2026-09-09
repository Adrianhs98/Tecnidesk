"""Router: admin_assistant — Endpoint for the shop administrator's Ohm assistant."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import admin_guard
from app.database import get_db
from app.models.user import User
from app.schemas.admin_assistant import AdminAssistantQueryRequest, AdminAssistantQueryResponse
from app.services import admin_assistant_service

router = APIRouter(
    prefix="/admin/assistant",
    tags=["Admin Assistant"],
)


@router.post(
    "/query",
    response_model=AdminAssistantQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar asistente administrativo Ohm",
    description=(
        "Permite al administrador consultar métricas operativas del taller mediante "
        "atajos rápidos o texto libre evaluado por un catálogo cerrado de intenciones."
    ),
)
async def query_admin_assistant(
    payload: AdminAssistantQueryRequest,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
) -> AdminAssistantQueryResponse:
    reply, intent, data = await admin_assistant_service.handle_admin_query(
        db=db,
        shop_id=current_user.shop_id,
        message=payload.message,
    )
    return AdminAssistantQueryResponse(
        reply=reply,
        intent=intent,
        data=data,
    )
