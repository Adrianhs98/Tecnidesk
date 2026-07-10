import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from decimal import Decimal
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.subscription import Subscription, SubscriptionStatusEnum
from app.models.shop import Shop
from app.models.plan import Plan

TARGET_SHOP_ID = "eac93993-7236-4a8b-a901-233733ecfd60"

async def add_subscription():
    async with AsyncSessionLocal() as session:
        # Check if shop exists
        shop = await session.scalar(select(Shop).where(Shop.id == TARGET_SHOP_ID))
        if not shop:
            print("❌ Shop no encontrado.")
            return

        # Fetch or create a plan
        plan = await session.scalar(select(Plan).limit(1))
        if not plan:
            plan = Plan(name="Pro Plan", price_usd=Decimal("29.99"))
            session.add(plan)
            await session.flush()
            print("✅ Plan de contingencia creado.")

        # Check existing subscription
        sub = await session.scalar(
            select(Subscription)
            .where(Subscription.shop_id == TARGET_SHOP_ID)
            .order_by(Subscription.started_at.desc())
            .limit(1)
        )
        
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=365)
        
        if sub:
            print(f"🔄 Actualizando suscripción existente: {sub.id}")
            sub.status = SubscriptionStatusEnum.active
            sub.ends_at = future
        else:
            print(f"➕ Creando nueva suscripción para el shop {TARGET_SHOP_ID}")
            new_sub = Subscription(
                shop_id=TARGET_SHOP_ID,
                plan_id=plan.id,
                status=SubscriptionStatusEnum.active,
                started_at=now,
                ends_at=future
            )
            session.add(new_sub)

        await session.commit()
        print("✅ ¡Suscripción activa añadida a la base de datos de manera exitosa!")

if __name__ == "__main__":
    asyncio.run(add_subscription())
