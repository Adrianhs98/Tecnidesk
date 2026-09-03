import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings
from app.models.shop import Shop
import uuid

# We will test the actual endpoints using TestClient.
# We need an auth token or we can override the dependency.
from app.core.dependencies import subscription_guard, get_current_user

# Find a real shop in the DB or just mock the dependency to return a dummy shop object.
# But wait, the DB needs a real shop_id to insert into the inventory table!
# Let's query the DB for a real shop.
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def get_real_shop_id():
    settings = get_settings()
    engine = create_async_engine(settings.db_url)
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT id FROM shops LIMIT 1;"))
        row = result.fetchone()
        if row:
            return row[0]
        return None

def run_test():
    shop_id = asyncio.run(get_real_shop_id())
    if not shop_id:
        print("No shop found in DB")
        return

    # Override dependencies
    mock_shop = Shop(id=shop_id, subdomain="test", business_name="Test Shop")
    app.dependency_overrides[subscription_guard] = lambda: mock_shop
    
    # We also might need get_current_user if the router uses it? No, the router only uses subscription_guard.
    
    client = TestClient(app)
    print("Testing POST /inventory...")
    payload = {
        "item_name": "Test Integration Item",
        "stock_quantity": 5,
        "cost_price": 2.50,
        "selling_price": 5.00,
        "low_stock_alert": 2
    }
    # It might be registered at /api/v1/inventory or /inventory. Let's try /inventory since main.py has app.include_router(inventory.router) without prefix.
    # Wait, in routers/inventory.py, does it have a prefix? 
    res = client.post("/inventory", json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    run_test()
