"""
Seed script — Inserta datos iniciales en la base de datos.

IDEMPOTENTE (A12): Puede ejecutarse múltiples veces sin duplicar datos.
Usa INSERT ... ON CONFLICT DO NOTHING para evitar errores en re-ejecuciones.

Uso:
    python scripts/seed.py
"""
import asyncio
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()


async def seed_plans(session: AsyncSession) -> None:
    """
    Inserta el plan 'Todo Incluido' si aún no existe (A12: idempotente).
    Verifica por nombre antes de insertar para evitar duplicados.
    """
    # Verificar si ya existe antes de insertar
    result = await session.execute(
        text("SELECT id FROM plans WHERE name = 'Todo Incluido' LIMIT 1")
    )
    existing = result.scalar_one_or_none()

    if existing:
        print("ℹ️  Plan 'Todo Incluido' ya existe — omitiendo inserción.")
        return

    # Insertar el plan inicial
    await session.execute(
        text("""
            INSERT INTO plans (id, name, price_usd, is_active)
            VALUES (gen_random_uuid(), 'Todo Incluido', 17.00, true)
        """)
    )
    print("✅ Plan 'Todo Incluido' ($17.00 USD) insertado correctamente.")


async def main() -> None:
    """Punto de entrada del seed."""
    print("🌱 Iniciando seed de TecniDesk...")

    engine = create_async_engine(settings.db_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with async_session() as session:
            async with session.begin():
                await seed_plans(session)
        print("✅ Seed completado exitosamente.")
    except Exception as exc:
        print(f"❌ Error durante el seed: {exc}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
