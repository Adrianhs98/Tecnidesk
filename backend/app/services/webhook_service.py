"""
Servicio: webhook_service — Despacho y registro de notificaciones HTTP (Webhooks).

Implementa:
  - Firma segura HMAC SHA-256 (si webhook_secret está configurado).
  - Tarea en segundo plano asíncrona (fire-and-forget).
  - Reintentos con retroceso exponencial (Backoff).
  - Aislamiento de sesión de base de datos para evitar colisiones con la petición HTTP original.
"""
import asyncio
import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone
import httpx
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.webhook_log import WebhookLog, WebhookStatusEnum
from app.models.ticket import Ticket

logger = logging.getLogger("tecnidesk.webhook_service")


async def notify(
    db: AsyncSession,
    ticket: Ticket,
    event_type: str,
    payload: dict,
) -> None:
    """
    Envia una notificación webhook en segundo plano.
    
    Inicia una corrutina asyncio.create_task para evitar bloquear la transacción
    o el request original del usuario.
    """
    settings = get_settings()
    webhook_url = settings.webhook_url
    webhook_secret = settings.webhook_secret

    if not webhook_url:
        logger.info("Envío de webhook omitido: settings.webhook_url no está configurado.")
        return

    # Creamos la tarea en segundo plano pasando los identificadores y datos
    # planos. No pasamos el objeto ORM 'ticket' directamente ya que
    # está vinculado a la sesión de base de datos original que será cerrada pronto.
    asyncio.create_task(
        _dispatch_async_task(
            ticket_id=ticket.id,
            event_type=event_type,
            payload=payload,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
        )
    )


async def _dispatch_async_task(
    ticket_id: uuid.UUID,
    event_type: str,
    payload: dict,
    webhook_url: str,
    webhook_secret: str,
) -> None:
    """
    Realiza la petición HTTP, firma el payload y escribe el log de auditoría
    en base de datos de forma aislada y resiliente.
    """
    payload_str = json.dumps(payload, ensure_ascii=False)

    # 1. Crear el log inicial en estado 'pending' con una nueva sesión dedicada
    async with AsyncSessionLocal() as db_session:
        log_entry = WebhookLog(
            ticket_id=ticket_id,
            event_type=event_type,
            webhook_url=webhook_url,
            payload=payload_str,
            status=WebhookStatusEnum.pending,
            attempts=0,
        )
        db_session.add(log_entry)
        await db_session.commit()
        await db_session.refresh(log_entry)
        log_id = log_entry.id

    # 2. Configurar cabeceras y firma HMAC
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "TecniDesk-Webhook/1.0",
        "X-TecniDesk-Event": event_type,
    }

    if webhook_secret:
        signature = hmac.new(
            webhook_secret.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        headers["X-TecniDesk-Signature"] = signature

    max_attempts = 3
    final_status = WebhookStatusEnum.failed
    response_status = None
    response_body = None

    async with httpx.AsyncClient(timeout=8.0) as client:
        for attempt in range(1, max_attempts + 1):
            # Registrar el intento actual en la DB
            async with AsyncSessionLocal() as db_session:
                stmt_log = await db_session.get(WebhookLog, log_id)
                if stmt_log:
                    stmt_log.attempts = attempt
                    if attempt > 1:
                        stmt_log.status = WebhookStatusEnum.retrying
                    await db_session.commit()

            try:
                response = await client.post(
                    webhook_url,
                    content=payload_str,
                    headers=headers,
                )
                response_status = response.status_code
                response_body = response.text[:1500]  # Cap de seguridad para base de datos

                if 200 <= response.status_code < 300:
                    final_status = WebhookStatusEnum.sent
                    break
                else:
                    final_status = WebhookStatusEnum.failed

            except httpx.RequestError as exc:
                logger.warning(
                    f"Intento {attempt} de webhook fallido para el ticket {ticket_id}: {exc}"
                )
                response_body = f"Excepción de conexión HTTP: {type(exc).__name__} - {exc}"
                final_status = WebhookStatusEnum.failed

            # Retroceso exponencial (Exponential Backoff): 2s, 4s...
            if attempt < max_attempts:
                await asyncio.sleep(2**attempt)

    # 3. Guardar el estado final del webhook en base de datos
    async with AsyncSessionLocal() as db_session:
        stmt_log = await db_session.get(WebhookLog, log_id)
        if stmt_log:
            stmt_log.status = final_status
            stmt_log.response_status = response_status
            stmt_log.response_body = response_body
            if final_status == WebhookStatusEnum.sent:
                stmt_log.sent_at = datetime.now(timezone.utc)
            await db_session.commit()

    logger.info(
        f"Webhook de tipo {event_type} para el ticket {ticket_id} procesado con estado final: {final_status.value}."
    )
