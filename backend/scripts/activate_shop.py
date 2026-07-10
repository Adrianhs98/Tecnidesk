import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.shop import Shop
from app.models.subscription import SubscriptionStatusEnum

async def activate_shops():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Shop))
        shops = result.scalars().all()
        
        if not shops:
            print("❌ No hay talleres en la base de datos.")
            return
            
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=365) # 1 year future
            
        for shop in shops:
            shop.subscription_status = SubscriptionStatusEnum.active
            shop.trial_ends_at = future
            
        await session.commit()
        
        print("\n" + "="*50)
        print(f"✅ Se actualizaron {len(shops)} talleres a estado 'ACTIVE'")
        print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(activate_shops())
