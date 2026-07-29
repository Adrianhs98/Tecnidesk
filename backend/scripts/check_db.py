import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import sys

from app.config import get_settings

async def main():
    settings = get_settings()
    engine = create_async_engine(settings.db_url)
    try:
        async with engine.begin() as conn:
            # Query the columns of the inventory table
            result = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='inventory';"
            ))
            columns = [row[0] for row in result.fetchall()]
            print("Columns in 'inventory' table:", columns)
            if "is_active" in columns:
                print("SUCCESS: 'is_active' column EXISTS in the database.")
            else:
                print("ERROR: 'is_active' column is MISSING.")
    except Exception as e:
        print("Database error:", e)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
