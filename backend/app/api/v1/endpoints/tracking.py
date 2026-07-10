from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.ticket import PublicTicketResponse
from app.services import ticket_service
from app.services.email_service import send_approval_email

router = APIRouter()


def _enrich_response(ticket) -> dict:
    """Construye la respuesta pública incluyendo contact_whatsapp del shop."""
    data = {
        "device_brand": ticket.device_brand,
        "device_model": ticket.device_model,
        "issue_description": ticket.issue_description,
        "status": ticket.status,
        "diagnostic_notes": ticket.diagnostic_notes,
        "total_cost": ticket.total_cost,
        "requires_approval": ticket.requires_approval,
        "tracking_token": ticket.tracking_token,
        "contact_whatsapp": (getattr(ticket.shop, "contact_whatsapp", None) or None) if ticket.shop else None,
        "evidences": getattr(ticket, "evidences", []) or [],
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "shop_name": getattr(ticket.shop, "business_name", None) if ticket.shop else None,
        "shop_logo_url": getattr(ticket.shop, "logo_url", None) if ticket.shop else None,
    }
    return data


@router.get("/{tracking_token}", response_model=PublicTicketResponse)
async def get_public_ticket(
    tracking_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene la información pública de un ticket de reparación usando el tracking_token.
    Este endpoint no requiere autenticación y es usado por los clientes finales.
    """
    ticket = await ticket_service.get_ticket_by_tracking_token(db, tracking_token)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )
        
    return _enrich_response(ticket)


@router.post("/{tracking_token}/approve", response_model=PublicTicketResponse)
async def approve_ticket(
    tracking_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Aprueba el presupuesto de un ticket (público, sin JWT).
    Cambia el status de ESPERANDO_APROBACION a EN_REPARACION.
    """
    ticket = await ticket_service.approve_ticket_by_token(db, tracking_token)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )

    # Enviar email de notificación al taller (no bloquea si falla)
    try:
        if ticket.shop and ticket.shop.contact_email:
            await send_approval_email(
                to_email=ticket.shop.contact_email,
                ticket=ticket,
                shop=ticket.shop,
            )
    except Exception as e:
        print(f"⚠️ Error al enviar email de aprobación: {e}")

    return _enrich_response(ticket)


@router.post("/{tracking_token}/reject", response_model=PublicTicketResponse)
async def reject_ticket(
    tracking_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Rechaza el presupuesto de un ticket (público, sin JWT).
    Cambia el status de ESPERANDO_APROBACION a NO_APROBADO.
    """
    ticket = await ticket_service.reject_ticket_by_token(db, tracking_token)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket no encontrado"
        )

    return _enrich_response(ticket)

