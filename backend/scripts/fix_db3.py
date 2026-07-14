import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def fix_views_and_column():
    async with AsyncSessionLocal() as session:
        # Create ENUM type
        try:
            await session.execute(text("CREATE TYPE item_type_enum AS ENUM ('part', 'labor', 'other');"))
            await session.commit()
            print("ENUM creado exitosamente.")
        except Exception as e:
            await session.rollback()
            print(f"ENUM ya existe o error: {e}")
            
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
            await session.rollback()
            return
            
        # 3. Recreate views
        for v_name, v_def in views:
            # We must fix the view definitions since they might have cast to 'part'::text which now needs to be 'part'::item_type_enum
            # Actually, the view definitions were dumped, we can just replace 'part'::text with 'part'::item_type_enum if needed, or PostgreSQL might auto-cast it.
            # But the views definition as dumped earlier already had syntax like "((ti.item_type)::text = 'part'::text)" which means it casts item_type to text.
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
