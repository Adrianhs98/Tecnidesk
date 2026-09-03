"""
Servicio: shop_service — Lógica de creación de talleres.

Regla 1:  Al crear un shop, generar trial_ends_at = now() + 30 días y
          crear automáticamente un registro en subscriptions con status='trial'.

Riesgo 2: POST /shops recibe admin_email + admin_password.
          Crear shop + subscription + primer usuario admin en la MISMA transacción.
          admin_password se hashea con bcrypt. NUNCA sale de este módulo en texto plano.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.plan import Plan
from app.models.shop import Shop, SubscriptionStatusEnum as ShopStatusEnum
from app.models.subscription import Subscription, SubscriptionStatusEnum as SubStatusEnum
from app.models.user import User, UserRoleEnum
from app.schemas.shop import ShopCreate


async def create_shop(db: AsyncSession, data: ShopCreate) -> tuple[Shop, str]:
    """
    Crea un nuevo taller con trial de 30 días, su suscripción inicial
    y el primer usuario administrador — todo en una única transacción atómica.

    Pasos:
      1. Obtener el plan activo más reciente.
      2. Calcular trial_ends_at = UTC now + 30 días.
      3. Insertar Shop con subscription_status='trial'.
      4. Flush para obtener shop.id.
      5. Insertar Subscription (fuente de verdad — D1).
      6. Insertar User admin con password hasheado con bcrypt.
      7. Flush final — commit lo gestiona la dependency get_db().

    Returns:
        (Shop ORM objeto, admin_email string)

    Raises:
        ValueError: si no hay planes activos en DB (falta seed).
    """
    now = datetime.now(timezone.utc)
    trial_ends_at = now + timedelta(days=30)

    # Paso 1: Obtener el plan activo
    result = await db.execute(
        select(Plan).where(Plan.is_active == True).limit(1)  # noqa: E712
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ValueError(
            "No hay planes activos en la base de datos. "
            "Ejecuta el seed script antes de crear talleres."
        )

    # Paso 2-3: Crear el shop
    shop = Shop(
        business_name=data.business_name,
        owner_name=data.owner_name,
        subdomain=data.subdomain,
        whatsapp_session_name=data.whatsapp_session_name,
        subscription_status=ShopStatusEnum.trial,
        trial_ends_at=trial_ends_at,
        created_at=now,
    )
    db.add(shop)

    # Paso 4: Flush para obtener shop.id antes de usarlo en FKs
    await db.flush()

    # Paso 5: Crear la suscripción trial (fuente de verdad — D1)
    subscription = Subscription(
        shop_id=shop.id,
        plan_id=plan.id,
        status=SubStatusEnum.trial,
        started_at=now,
        ends_at=trial_ends_at,
        payment_reference=None,
    )
    db.add(subscription)

    # Paso 6: Crear primer usuario admin — password hasheado, nunca en claro (Riesgo 2)
    admin_user = User(
        shop_id=shop.id,
        role=UserRoleEnum.admin,
        full_name=data.owner_name,
        email=str(data.admin_email),
        password_hash=hash_password(data.admin_password),  # bcrypt rounds=BCRYPT_ROUNDS
        is_active=True,
        created_at=now,
    )
    db.add(admin_user)

    # Paso 7: Flush final — commit gestionado por get_db()
    await db.flush()

    return shop, str(data.admin_email)


# ─── SLA Multi-tenant Configuration ──────────────────────────────────────────

DEFAULT_SLA_THRESHOLDS_HOURS: dict[str, int] = {
    "EN_ESPERA_INGRESO": 48,
    "EN_REVISION": 24,
    "EN_REPARACION": 48,
}


def get_effective_sla_thresholds(
    custom_thresholds: dict[str, int] | None = None,
) -> dict[str, int]:
    """
    Combina los umbrales de SLA por defecto del sistema con las personalizaciones del taller.
    Cualquier estado no configurado hereda de forma transparente el valor por defecto.
    """
    effective = dict(DEFAULT_SLA_THRESHOLDS_HOURS)
    if custom_thresholds:
        for key, val in custom_thresholds.items():
            if (
                key in DEFAULT_SLA_THRESHOLDS_HOURS
                and isinstance(val, int)
                and not isinstance(val, bool)
                and 1 <= val <= 720
            ):
                effective[key] = val
    return effective


async def get_shop_sla_config(
    db: AsyncSession,
    shop_id: uuid.UUID | str,
) -> dict:
    """
    Recupera la configuración de SLA del taller con umbrales efectivos,
    customs configurados y defaults del sistema.
    """
    stmt = select(Shop).where(Shop.id == shop_id)
    result = await db.execute(stmt)
    shop = result.scalar_one_or_none()
    if shop is None:
        raise ValueError(f"Taller {shop_id} no encontrado.")

    custom_thresholds = shop.sla_config or {}
    effective_thresholds = get_effective_sla_thresholds(custom_thresholds)

    return {
        "effective_thresholds": effective_thresholds,
        "custom_thresholds": custom_thresholds,
        "default_thresholds": dict(DEFAULT_SLA_THRESHOLDS_HOURS),
    }


async def update_shop_sla_config(
    db: AsyncSession,
    shop_id: uuid.UUID | str,
    custom_thresholds: dict[str, int],
) -> dict:
    """
    Actualiza la configuración de SLA del taller persistiendo el JSON en shops.sla_config.
    """
    stmt = select(Shop).where(Shop.id == shop_id)
    result = await db.execute(stmt)
    shop = result.scalar_one_or_none()
    if shop is None:
        raise ValueError(f"Taller {shop_id} no encontrado.")

    # Sanitizar claves y valores antes de persistir
    cleaned_custom = {
        k: v
        for k, v in custom_thresholds.items()
        if (
            k in DEFAULT_SLA_THRESHOLDS_HOURS
            and isinstance(v, int)
            and not isinstance(v, bool)
            and 1 <= v <= 720
        )
    }

    shop.sla_config = cleaned_custom
    db.add(shop)
    await db.flush()

    effective_thresholds = get_effective_sla_thresholds(cleaned_custom)

    return {
        "effective_thresholds": effective_thresholds,
        "custom_thresholds": cleaned_custom,
        "default_thresholds": dict(DEFAULT_SLA_THRESHOLDS_HOURS),
    }


