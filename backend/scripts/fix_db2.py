import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text
import json

async def fix_views_and_column():
    async with AsyncSessionLocal() as session:
        # Get views definition
        result = await session.execute(text("""
            SELECT table_name, view_definition 
            FROM information_schema.views 
            WHERE table_schema = 'public' 
              AND view_definition ILIKE '%ticket_items%';
        """))
        
        views = [(row[0], row[1]) for row in result]
        print(f"Encontradas {len(views)} vistas dependientes:")
        
        for v_name, v_def in views:
            print(f"- {v_name}")
            
        # 1. Drop views
        for v_name, v_def in views:
            await session.execute(text(f"DROP VIEW IF EXISTS {v_name} CASCADE;"))
            print(f"Dropped {v_name}")
            
        # 2. Alter column
        try:
            await session.execute(text("ALTER TABLE ticket_items ALTER COLUMN item_type DROP DEFAULT;"))
            await session.execute(text("ALTER TABLE ticket_items ALTER COLUMN item_type TYPE item_type_enum USING item_type::item_type_enum;"))
            await session.execute(text("ALTER TABLE ticket_items ALTER COLUMN item_type SET DEFAULT 'part'::item_type_enum;"))
            print("Columna convertida a ENUM exitosamente.")
        except Exception as e:
            print(f"Error alterando columna: {e}")
            
        # 3. Recreate views
        for v_name, v_def in views:
            # information_schema.views returns a CREATE VIEW definition without the "CREATE VIEW v_name AS" part.
            # Actually, view_definition is just the SELECT statement.
            create_stmt = f"CREATE OR REPLACE VIEW {v_name} AS {v_def}"
            try:
                await session.execute(text(create_stmt))
                print(f"Recreated {v_name}")
            except Exception as e:
                print(f"Error recreating {v_name}: {e}")
                
        await session.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_views_and_column())
