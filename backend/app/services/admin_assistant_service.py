"""
Service: admin_assistant_service
Provides intent classification, deterministic metric queries, and natural language formatting
for the administrator's conversational interface with Ohm.
"""
from __future__ import annotations

import datetime
from datetime import timezone, timedelta
import logging
import re
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from google import genai
from google.genai import types
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ticket import Ticket, TicketStatusEnum

logger = logging.getLogger(__name__)

INTENT_GANANCIAS_DEL_DIA = "ganancias_del_dia"
INTENT_EQUIPOS_INGRESADOS_HOY = "equipos_ingresados_hoy"
INTENT_EQUIPOS_SIN_TOCAR = "equipos_sin_tocar"
INTENT_NONE = "NONE"

SUPPORTED_INTENTS = {
    INTENT_GANANCIAS_DEL_DIA,
    INTENT_EQUIPOS_INGRESADOS_HOY,
    INTENT_EQUIPOS_SIN_TOCAR,
}

CANNED_HELP_RESPONSE = (
    "Actualmente puedo asistirte con las siguientes consultas operativas sobre tu taller:\n\n"
    "• 💰 **Ganancias del día**: Facturación de reparaciones completadas y listas para entregar hoy.\n"
    "• 📥 **Equipos ingresados hoy**: Conteo de nuevas órdenes de servicio recibidas hoy.\n"
    "• ⏱️ **Equipos sin tocar**: Órdenes de trabajo activas sin actualizaciones por más de 48 horas.\n\n"
    "Podés pulsar cualquiera de los atajos rápidos de arriba o escribirme sobre estas métricas."
)


def _match_direct_intent(message: str) -> Optional[str]:
    """
    Fast regex / keyword matching for common shortcut queries.
    Avoids LLM latency when the user clicks a chip or sends exact phrases.
    """
    norm = re.sub(r"\s+", " ", message.strip().lower())
    # Remove accents for normalization
    norm = norm.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

    # 1. Ganancias del día
    if any(k in norm for k in [
        "ganancias de hoy", "ganancias del dia", "cuanto hemos ganado hoy",
        "cuanto gane hoy", "ingresos de hoy", "ventas de hoy", "total ganado hoy",
        "recaudacion de hoy", "facturacion de hoy", "cuanto dinero entro hoy",
        "ganancia hoy"
    ]):
        return INTENT_GANANCIAS_DEL_DIA

    # 2. Equipos ingresados hoy
    if any(k in norm for k in [
        "equipos ingresados hoy", "equipos ingresados", "cuantos equipos entraron hoy",
        "cuantos equipos ingresaron hoy", "tickets ingresados hoy", "equipos nuevos hoy",
        "ordenes de hoy", "ordenes ingresadas hoy", "equipos recibidos hoy",
        "ingresos de hoy"
    ]):
        return INTENT_EQUIPOS_INGRESADOS_HOY

    # 3. Equipos sin tocar
    if any(k in norm for k in [
        "equipos sin tocar", "tickets sin tocar", "equipos parados", "equipos varados",
        "equipos estancados", "ordenes sin tocar", "equipos sin avance", "tickets sin avance",
        "equipos demorados", "equipos retrasados"
    ]):
        return INTENT_EQUIPOS_SIN_TOCAR

    return None


async def classify_intent(message: str) -> str:
    """
    Classifies the user message into one of the closed catalog intents or INTENT_NONE.
    Uses pattern matching first, falling back to gemini-3.5-flash-lite.
    """
    direct = _match_direct_intent(message)
    if direct:
        return direct

    settings = get_settings()
    if not settings.gemini_api_key:
        return INTENT_NONE

    prompt = (
        "Sos un clasificador de intenciones para el software de talleres de reparación TecniDesk.\n"
        "Clasificá la consulta del administrador estrictamente en uno de los siguientes 4 intents:\n"
        "- ganancias_del_dia: preguntas sobre dinero ganado, ventas, facturación o ingresos de hoy.\n"
        "- equipos_ingresados_hoy: preguntas sobre cantidad de celulares/equipos/tickets ingresados o recibidos hoy.\n"
        "- equipos_sin_tocar: preguntas sobre equipos estancados, sin avance, sin tocar o sin cambios hace días/horas.\n"
        "- NONE: cualquier otra consulta que no corresponda a ninguno de los anteriores o que sea una charla informal.\n\n"
        "Respondé ÚNICAMENTE con el token del intent (sin explicaciones, sin puntuación):\n"
        f"Consulta: {message}"
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.gemini_fast_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=20),
        )
        token = (response.text or "").strip().lower()
        if token in SUPPORTED_INTENTS:
            return token
        for intent in SUPPORTED_INTENTS:
            if intent in token:
                return intent
        return INTENT_NONE
    except Exception as exc:
        logger.warning("Error classifying admin intent via LLM: %s", exc)
        return INTENT_NONE


async def execute_daily_revenue(db: AsyncSession, shop_id: uuid.UUID) -> Dict[str, Any]:
    """Calculates total revenue from tickets completed / ready for pickup today."""
    now = datetime.datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            func.coalesce(func.sum(Ticket.total_cost), 0).label("total_revenue"),
            func.count(Ticket.id).label("completed_count"),
        ).where(
            Ticket.shop_id == shop_id,
            Ticket.status == TicketStatusEnum.LISTO_PARA_RETIRAR,
            Ticket.updated_at >= start_of_today,
        )
    )
    row = result.one()
    total = float(row.total_revenue) if row.total_revenue is not None else 0.0
    count = int(row.completed_count) if row.completed_count is not None else 0
    return {
        "total_revenue": total,
        "formatted_revenue": f"${total:.2f} USD",
        "completed_count": count,
        "date": start_of_today.strftime("%Y-%m-%d"),
    }


async def execute_daily_intake(db: AsyncSession, shop_id: uuid.UUID) -> Dict[str, Any]:
    """Counts the number of tickets registered today."""
    now = datetime.datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.count(Ticket.id)).where(
            Ticket.shop_id == shop_id,
            Ticket.created_at >= start_of_today,
        )
    )
    count = result.scalar_one() or 0
    return {
        "intake_count": int(count),
        "date": start_of_today.strftime("%Y-%m-%d"),
    }


async def execute_untouched_tickets(db: AsyncSession, shop_id: uuid.UUID) -> Dict[str, Any]:
    """Finds active tickets without updates for more than 48 hours."""
    now = datetime.datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=48)

    active_statuses = [
        TicketStatusEnum.EN_ESPERA_INGRESO,
        TicketStatusEnum.EN_REVISION,
        TicketStatusEnum.ESPERANDO_APROBACION,
        TicketStatusEnum.ESPERANDO_REPUESTO,
        TicketStatusEnum.EN_REPARACION,
    ]

    result = await db.execute(
        select(
            Ticket.id,
            Ticket.device_brand,
            Ticket.device_model,
            Ticket.status,
            Ticket.updated_at,
        ).where(
            Ticket.shop_id == shop_id,
            Ticket.status.in_(active_statuses),
            Ticket.updated_at <= cutoff,
        ).order_by(Ticket.updated_at.asc())
    )
    rows = result.all()

    items = []
    for r in rows:
        updated = r.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        hours_elapsed = max(0.0, (now - updated).total_seconds() / 3600.0)
        items.append({
            "brand": r.device_brand,
            "model": r.device_model,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "hours_stale": round(hours_elapsed, 1),
        })

    return {
        "stale_count": len(items),
        "sample_tickets": items[:3],
    }


async def format_response(intent: str, data: Dict[str, Any], user_message: str) -> str:
    """
    Synthesizes a friendly, natural Spanish response based on real deterministic metrics.
    If fast LLM is available, generates a dynamic response grounded on the numbers;
    otherwise returns a clean deterministic template.
    """
    # Deterministic templates as primary or fallback
    if intent == INTENT_GANANCIAS_DEL_DIA:
        rev = data.get("total_revenue", 0.0)
        cnt = data.get("completed_count", 0)
        fallback = (
            f"Hoy se han registrado **${rev:.2f} USD** en reparaciones completadas y listas para entregar"
            f"{f' ({cnt} equipos)' if cnt > 0 else ''}."
        )
    elif intent == INTENT_EQUIPOS_INGRESADOS_HOY:
        count = data.get("intake_count", 0)
        fallback = f"Hoy se han ingresado **{count}** {'equipo' if count == 1 else 'equipos'} nuevos al taller."
    elif intent == INTENT_EQUIPOS_SIN_TOCAR:
        stale = data.get("stale_count", 0)
        samples = data.get("sample_tickets", [])
        if stale == 0:
            fallback = "¡Excelente! No hay equipos activos que lleven más de 48 horas sin registrar cambios."
        else:
            sample_str = ""
            if samples:
                device_names = [f"{s['brand']} {s['model']} ({int(s['hours_stale'])}h)" for s in samples]
                sample_str = f" Algunos de ellos: {', '.join(device_names)}."
            fallback = (
                f"Hay **{stale}** {'equipo' if stale == 1 else 'equipos'} activos en el taller sin registrar movimiento "
                f"hace más de 48 horas.{sample_str}"
            )
    else:
        return CANNED_HELP_RESPONSE

    settings = get_settings()
    if not settings.gemini_api_key:
        return fallback

    prompt = (
        "Sos Ohm, el asistente inteligente de gestión de TecniDesk para administradores de talleres de reparación celular.\n"
        "A partir de los siguientes datos VERIFICADOS, redactá una respuesta amigable, concisa (máximo 2 oraciones) y profesional en español.\n"
        "Regla estricta: Mencioná los montos con símbolo de dólar $ y dos decimales (ejemplo: $245.50 USD). "
        "Usá los números exactos de los datos; no inventes cifras ni porcentajes que no estén en la entrada.\n\n"
        f"Datos reales: {data}\n"
        f"Consulta del administrador: {user_message}\n"
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=settings.gemini_fast_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=100),
        )
        text = (response.text or "").strip()
        return text if text else fallback
    except Exception as exc:
        logger.warning("Error generating conversational response via fast model: %s", exc)
        return fallback


async def handle_admin_query(
    db: AsyncSession,
    shop_id: uuid.UUID,
    message: str,
) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
    """
    Main orchestration entrypoint for admin queries:
    1. Classify intent
    2. If NONE: return canned response without touching database
    3. If recognized: execute deterministic query and format response
    """
    intent = await classify_intent(message)

    if intent == INTENT_NONE:
        return CANNED_HELP_RESPONSE, None, None

    if intent == INTENT_GANANCIAS_DEL_DIA:
        data = await execute_daily_revenue(db, shop_id)
    elif intent == INTENT_EQUIPOS_INGRESADOS_HOY:
        data = await execute_daily_intake(db, shop_id)
    elif intent == INTENT_EQUIPOS_SIN_TOCAR:
        data = await execute_untouched_tickets(db, shop_id)
    else:
        return CANNED_HELP_RESPONSE, None, None

    reply = await format_response(intent, data, message)
    return reply, intent, data
