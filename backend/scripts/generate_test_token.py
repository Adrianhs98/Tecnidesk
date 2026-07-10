import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token

async def generate_token():
    async with AsyncSessionLocal() as session:
        target_shop_id = "eac93993-7236-4a8b-a901-233733ecfd60"
        result = await session.execute(select(User).where(User.shop_id == target_shop_id))
        user = result.scalars().first()
        
        if not user:
            print(f"❌ No hay usuarios en la base de datos para el shop {target_shop_id}.")
            return
            
        token = create_access_token(
            user_id=str(user.id),
            shop_id=str(user.shop_id),
            role=user.role.value
        )
        
        print("\n" + "="*50)
        print("✅ TOKEN GENERADO EXITOSAMENTE")
        print("="*50)
        print(f"Usuario: {user.email}")
        print(f"Rol: {user.role.value}")
        print(f"Shop ID: {user.shop_id}")
        print("-" * 50)
        print("Copia el siguiente token en Swagger (Authorize):")
        print("\n" + token + "\n")
        print("="*50 + "\n")
        
        with open("raw_token.txt", "w", encoding="utf-8") as f:
            f.write(token)

if __name__ == "__main__":
    asyncio.run(generate_token())
