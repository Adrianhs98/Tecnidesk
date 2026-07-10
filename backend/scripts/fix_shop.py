import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.subscription import SubscriptionStatusEnum

TARGET_SHOP_ID = "eac93993-7236-4a8b-a901-233733ecfd60"

async def fix_shop_and_get_customer():
    async with AsyncSessionLocal() as session:
        # 1. Update the shop
        print(f"🔍 Buscando shop {TARGET_SHOP_ID}...")
        result = await session.execute(
            select(Shop).where(Shop.id == TARGET_SHOP_ID)
        )
        shop = result.scalar_one_or_none()
        
        if not shop:
            print(f"❌ Shop {TARGET_SHOP_ID} no encontrado en DB.")
            return

        shop.subscription_status = SubscriptionStatusEnum.active
        shop.trial_ends_at = datetime(2027, 1, 1, tzinfo=timezone.utc)
        
        await session.commit()
        print(f"✅ Shop {shop.business_name} actualizado a ACTIVE con límite 2027-01-01.")

        # 2. Get a valid customer for this shop
        cust_result = await session.execute(
            select(Customer).where(Customer.shop_id == TARGET_SHOP_ID).limit(1)
        )
        customer = cust_result.scalar_one_or_none()
        
        print("\n" + "="*50)
        if customer:
            print("✅ DATOS VALIDADOS PARA SWAGGER")
            print(f"Shop ID: {shop.id}")
            print(f"Customer ID: {customer.id}")
            print(f"Customer Name: {customer.full_name}")
            print("Usa este Customer ID en tu payload JSON para crear el ticket.")
            
            with open("customer_data.txt", "w", encoding="utf-8") as f:
                f.write(f"Customer ID: {customer.id}\n")
                f.write(f"Shop ID: {shop.id}\n")
                f.write(f"Full Name: {customer.full_name}\n")
        else:
            print("❌ No hay clientes registrados en este taller.")
            print("Por favor, crea un cliente primero o usa el endpoint correspondiente.")
        print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(fix_shop_and_get_customer())
