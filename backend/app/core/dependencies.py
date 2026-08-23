"""
Dependencias de FastAPI — Fase 2.2

  get_current_user(...)   → Extrae y valida el Bearer JWT; devuelve User ORM.
  subscription_guard(...) → Verifica que la suscripción del taller esté activa.
                            Bloquea con HTTP 402 si está vencida o cancelada.

Uso típico en un endpoint protegido:

    from app.core.dependencies import subscription_guard
    from app.models.user import User

    @router.get("/mi-endpoint")
    async def mi_endpoint(
        current_user: User = Depends(subscription_guard),
    ):
        ...

`subscription_guard` encadena `get_current_user` internamente, por lo que un
endpoint que use `subscription_guard` NO necesita declarar `get_current_user`
por separado.
"""
from datetime import datetime, timezone
import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings

from app.core.security import verify_access_token
from app.database import get_db
from app.models.subscription import Subscription, SubscriptionStatusEnum
from app.models.user import User

# ─── Esquema Bearer ───────────────────────────────────────────────────────────
_bearer_scheme = HTTPBearer(
    scheme_name="JWT",
    description="Token de acceso obtenido en POST /auth/login (Bearer <access_token>).",
    auto_error=True,   # Lanza 403 automáticamente si falta el header Authorization
)

# Statuses que BLOQUEAN el acceso, independientemente de ends_at
_BLOCKING_STATUSES = {
    SubscriptionStatusEnum.suspended,
    SubscriptionStatusEnum.cancelled,
    SubscriptionStatusEnum.past_due,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency 1: get_current_user
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extrae el Bearer JWT del header Authorization, lo verifica y devuelve
    el User ORM correspondiente.

    Raises:
        HTTP 401: token inválido, expirado o usuario no encontrado/inactivo.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de acceso inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Verificar firma y expiración del JWT
    try:
        payload = verify_access_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # 2. Obtener usuario de la DB (verificar que siga existiendo y activo)
    result = await db.execute(
        select(User).where(User.id == user_id)  # type: ignore[arg-type]
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    request.state.user_id = str(user.id)
    request.state.shop_id = str(user.shop_id)

    return user


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency 2: subscription_guard
# ═══════════════════════════════════════════════════════════════════════════════

_SUBSCRIPTION_EXPIRED_MSG = (
    "Tu suscripción ha expirado. "
    "Contacta a soporte para reactivarla."
)

_PAYMENT_EXCEPTION = HTTPException(
    status_code=status.HTTP_402_PAYMENT_REQUIRED,
    detail=_SUBSCRIPTION_EXPIRED_MSG,
)


async def subscription_guard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Verifica que la suscripción del taller del usuario esté activa.

    Lee DIRECTAMENTE de la tabla `subscriptions` (fuente de verdad — D1).
    NO usa el campo denormalizado `shops.subscription_status`.

    Bloquea con HTTP 402 si:
      - No existe suscripción para el shop.
      - status es 'suspended', 'cancelled' o 'past_due'.
      - status es 'trial' o 'active' pero ends_at ya expiró.

    Returns:
        El mismo User ORM si la suscripción está vigente (para encadenamiento).

    Raises:
        HTTP 402: suscripción bloqueante o vencida.
        HTTP 401: propagado desde get_current_user si el token es inválido.
    """
    # Obtener la suscripción más reciente del taller (started_at DESC)
    result = await db.execute(
        select(Subscription)
        .where(Subscription.shop_id == current_user.shop_id)
        .order_by(Subscription.started_at.desc())
        .limit(1)
    )
    subscription = result.scalar_one_or_none()

    # Sin suscripción → acceso denegado
    if subscription is None:
        raise _PAYMENT_EXCEPTION

    # Status explícitamente bloqueante
    if subscription.status in _BLOCKING_STATUSES:
        raise _PAYMENT_EXCEPTION

    # Trial o active pero ends_at ha pasado
    if subscription.ends_at is not None:
        now = datetime.now(timezone.utc)
        if now > subscription.ends_at:
            raise _PAYMENT_EXCEPTION

    return current_user


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency 3: admin_guard
# ═══════════════════════════════════════════════════════════════════════════════

async def admin_guard(
    current_user: User = Depends(subscription_guard),
) -> User:
    """
    Extiende subscription_guard: además de suscripción activa,
    requiere role == 'admin'.
    """
    from app.models.user import UserRoleEnum
    if current_user.role != UserRoleEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador para esta acción."
        )
    return current_user


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency 4: superadmin_key_guard
# ═══════════════════════════════════════════════════════════════════════════════

_superadmin_key_scheme = APIKeyHeader(
    name="X-Superadmin-Key",
    auto_error=False,
    description="Clave de súper-administrador para operaciones de plataforma.",
)


async def superadmin_key_guard(
    api_key: str | None = Depends(_superadmin_key_scheme),
) -> str:
    """
    Verifica que la petición incluya el header X-Superadmin-Key con la clave
    configurada en SUPERADMIN_API_KEY. Usa secrets.compare_digest para evitar
    ataques de timing.

    Raises:
        HTTP 401: si el header X-Superadmin-Key no está presente.
        HTTP 403: si la clave proporcionada es incorrecta.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere la cabecera X-Superadmin-Key para esta acción.",
        )

    settings = get_settings()
    if not secrets.compare_digest(api_key, settings.superadmin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clave de superadministrador inválida.",
        )

    return api_key


# ═══════════════════════════════════════════════════════════════════════════════
# Dependency 5: verify_ticket_technician_access
# ═══════════════════════════════════════════════════════════════════════════════

async def verify_ticket_technician_access(
    ticket_id: str,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """
    Valida el acceso a un ticket para técnicos y administradores.
    
    Reglas:
    - Administradores tienen acceso a todos los tickets de su taller.
    - Técnicos solo pueden acceder a tickets asignados a ellos o sin asignar (NULL)
      para permitir su auto-asignación.
    - Si el ticket está asignado a otro técnico, lanza HTTP 403 Forbidden.
    - Si el ticket no existe en el taller del usuario, lanza HTTP 404 Not Found.
    """
    import uuid as _uuid
    from app.models.ticket import Ticket
    from app.models.technician import Technician
    from app.models.user import UserRoleEnum

    try:
        parsed_id = _uuid.UUID(str(ticket_id))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} no encontrado en este taller."
        )

    result = await db.execute(
        select(Ticket).where(Ticket.id == parsed_id, Ticket.shop_id == current_user.shop_id)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} no encontrado en este taller."
        )

    if current_user.role == UserRoleEnum.technician:
        # Si el ticket no tiene técnico asignado (None), se permite el acceso para auto-asignarse
        if ticket.technician_id is None and ticket.assigned_technician_id is None:
            return ticket

        # Buscar perfil del técnico por user_id en el mismo taller
        tech_res = await db.execute(
            select(Technician).where(
                Technician.user_id == current_user.id,
                Technician.shop_id == current_user.shop_id,
            )
        )
        tech_profile = tech_res.scalar_one_or_none()

        is_assigned_to_me = False
        if tech_profile and ticket.technician_id == tech_profile.id:
            is_assigned_to_me = True
        elif ticket.technician_id == current_user.id or ticket.assigned_technician_id == current_user.id:
            is_assigned_to_me = True

        if not is_assigned_to_me:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para acceder a un ticket asignado a otro técnico."
            )

    return ticket
