import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def fix_db():
    async with AsyncSessionLocal() as session:
        # Create ENUM type
        try:
            await session.execute(text("CREATE TYPE item_type_enum AS ENUM ('part', 'labor', 'other');"))
            print("ENUM creado exitosamente.")
        except Exception as e:
            print(f"ENUM ya existe o error: {e}")
            
        # Alter column from VARCHAR to ENUM
        try:
            # Drop default if exists
            await session.execute(text("ALTER TABLE ticket_items ALTER COLUMN item_type DROP DEFAULT;"))
            
            # Change type with a USING clause to cast existing varchar data to the new enum
            await session.execute(text("ALTER TABLE ticket_items ALTER COLUMN item_type TYPE item_type_enum USING item_type::item_type_enum;"))
            
            # Set default again
            await session.execute(text("ALTER TABLE ticket_items ALTER COLUMN item_type SET DEFAULT 'part'::item_type_enum;"))
            
            print("Columna convertida a ENUM exitosamente.")
        except Exception as e:
            print(f"Error al alterar la tabla: {e}")
            
        await session.commit()

if __name__ == "__main__":
    asyncio.run(fix_db())
