"""
Script operativo: Sincronización y vinculación de Técnicos existentes con Cuentas de Usuario.

Revisa los técnicos en la tabla `technicians` que no tengan `user_id` asignado,
crea su cuenta de usuario con rol `technician` y una contraseña temporal segura,
y vincula `technician.user_id = user.id`.

Uso:
    python scripts/sync_technicians_users.py
"""
import asyncio
import re
import unicodedata
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.technician import Technician
from app.models.user import User, UserRoleEnum
from app.models.shop import Shop
from app.core.security import hash_password, generate_random_password


def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)[:20]


async def sync_technicians():
    print("=== Sincronización de Técnicos a Cuentas de Usuario ===")
    async with AsyncSessionLocal() as session:
        # Obtener todos los técnicos sin user_id
        stmt = select(Technician).where(Technician.user_id.is_(None))
        result = await session.execute(stmt)
        technicians = list(result.scalars().all())

        if not technicians:
            print("Todos los técnicos ya cuentan con una cuenta de usuario vinculada.")
            return

        print(f"Se encontraron {len(technicians)} técnicos sin cuenta de usuario vinculada.\n")
        created_count = 0

        for tech in technicians:
            # Obtener datos del taller
            shop = await session.scalar(select(Shop).where(Shop.id == tech.shop_id))
            shop_domain = shop.subdomain if shop and shop.subdomain else f"shop_{tech.shop_id.hex[:6]}"

            # Derivar email para el técnico
            slug_name = _slugify(tech.full_name) or "tecnico"
            base_email = f"{slug_name}@{shop_domain}.tecnidesk.com"
            email = base_email

            # Verificar si ya existe un usuario con ese email
            counter = 1
            while True:
                existing_user = await session.scalar(select(User).where(User.email == email))
                if not existing_user:
                    break
                email = f"{slug_name}_{counter}@{shop_domain}.tecnidesk.com"
                counter += 1

            # Generar contraseña temporal segura
            plain_password = generate_random_password(12)
            pwd_hash = hash_password(plain_password)

            # Crear usuario
            user = User(
                shop_id=tech.shop_id,
                role=UserRoleEnum.technician,
                full_name=tech.full_name,
                email=email,
                password_hash=pwd_hash,
                is_active=tech.is_active,
            )
            session.add(user)
            await session.flush()

            # Vincular al técnico
            tech.user_id = user.id
            created_count += 1

            print(f"[VINCULADO] Técnico: {tech.full_name} (ID: {tech.id})")
            print(f"   Email:      {email}")
            print(f"   Contraseña: {plain_password}")
            print(f"   User ID:    {user.id}")
            print("-" * 50)

        await session.commit()
        print(f"\nProceso finalizado con éxito: {created_count} técnicos sincronizados y vinculados.")


if __name__ == "__main__":
    asyncio.run(sync_technicians())
