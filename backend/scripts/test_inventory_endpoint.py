import asyncio
from fastapi.testclient import TestClient
import uuid
import sys
from datetime import datetime
from unittest.mock import AsyncMock

from app.main import app
from app.core.dependencies import subscription_guard, get_db
from app.models.shop import Shop
from app.schemas.inventory import InventoryCreate, InventoryResponse

# Mock dependencies
mock_shop = Shop(id=uuid.uuid4(), subdomain="test-shop", business_name="Test Shop")

def override_subscription_guard():
    return mock_shop

class MockSession:
    pass

def override_get_db():
    yield MockSession()

app.dependency_overrides[subscription_guard] = override_subscription_guard
app.dependency_overrides[get_db] = override_get_db

# Patch the inventory service methods to avoid DB calls
from app.services import inventory_service
from app.models.inventory import Inventory
from decimal import Decimal

mock_item = Inventory(
    id=uuid.uuid4(),
    shop_id=mock_shop.id,
    item_name="Bateria Samsung A12",
    stock_quantity=10,
    cost_price=Decimal("5.00"),
    selling_price=Decimal("15.00"),
    low_stock_alert=3,
    is_active=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

async def mock_list_inventory(*args, **kwargs):
    return [mock_item]

async def mock_create_inventory_item(*args, **kwargs):
    # Simulate return
    return mock_item

inventory_service.list_inventory = mock_list_inventory
inventory_service.create_inventory_item = mock_create_inventory_item

client = TestClient(app)

def run_tests():
    print("Testing GET /inventory...")
    res = client.get("/api/v1/inventory") # Note: router prefix is usually registered on main
    # wait, the router might be at /inventory or /api/v1/inventory
    if res.status_code == 404:
        res = client.get("/inventory")
        
    print(f"GET /inventory status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"GET Response: {data}")
        if data and "is_low_stock" in data[0]:
            print("is_low_stock field is present:", data[0]["is_low_stock"])
        else:
            print("ERROR: is_low_stock missing in GET")
            sys.exit(1)
    else:
        print(f"GET Error: {res.text}")
        sys.exit(1)

    print("\nTesting POST /inventory...")
    payload = {
        "item_name": "Test Item",
        "stock_quantity": 5,
        "cost_price": 2.50,
        "selling_price": 5.00,
        "low_stock_alert": 2
    }
    res = client.post("/inventory", json=payload)
    if res.status_code == 404:
         res = client.post("/api/v1/inventory", json=payload)
         
    print(f"POST /inventory status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"POST Response: {data}")
        if "is_low_stock" in data:
            print("is_low_stock field is present:", data["is_low_stock"])
        else:
            print("ERROR: is_low_stock missing in POST")
            sys.exit(1)
    else:
        print(f"POST Error: {res.text}")
        sys.exit(1)
        
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    run_tests()
