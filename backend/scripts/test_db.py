import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check_db():
    async with AsyncSessionLocal() as session:
        # Check column types
        result = await session.execute(text("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'ticket_items';
        """))
        print("--- ticket_items columns ---")
        for row in result:
            print(f"{row[0]}: {row[1]} ({row[2]})")
            
        # Check if item_type_enum exists
        result = await session.execute(text("""
            SELECT typname 
            FROM pg_type 
            WHERE typname = 'item_type_enum';
        """))
        types = result.scalars().all()
        print("\n--- ENUM types ---")
        print(types)

if __name__ == "__main__":
    asyncio.run(check_db())
