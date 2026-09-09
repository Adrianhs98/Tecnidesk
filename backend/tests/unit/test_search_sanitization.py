from datetime import datetime, timezone
import uuid
from decimal import Decimal
import pytest

from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.shop import Shop
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.user import User, UserRoleEnum
from app.routers.inventory import list_inventory
from app.services.client_service import ClientService
from app.services.ticket_service import list_tickets


async def _seed_common(db_session):
    now = datetime.now(timezone.utc)
    shop = Shop(
        business_name="Search Sanitization Shop",
        owner_name="Owner",
        subdomain=f"search-{uuid.uuid4().hex[:8]}",
        contact_email="search@example.com",
        contact_whatsapp="0991234567",
        created_at=now,
    )
    db_session.add(shop)
    await db_session.flush()

    user = User(
        email=f"admin-{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hash",
        full_name="Shop Admin",
        shop_id=shop.id,
        role=UserRoleEnum.admin,
    )
    db_session.add(user)
    await db_session.flush()
    return shop, user


@pytest.mark.asyncio
async def test_ticket_search_sanitization_whitespace_returns_all(db_session):
    shop, _ = await _seed_common(db_session)
    customer = Customer(
        shop_id=shop.id,
        full_name="Juan Perez",
        phone_number="0991111111",
        email="juan@example.com",
    )
    db_session.add(customer)
    await db_session.flush()

    t1 = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        device_brand="Samsung",
        device_model="Galaxy A54",
        issue_description="Pantalla rota",
        status=TicketStatusEnum.EN_REVISION,
    )
    t2 = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Bateria hinchada",
        status=TicketStatusEnum.EN_REVISION,
    )
    db_session.add_all([t1, t2])
    await db_session.flush()

    # Whitespace-only search must NOT filter out all tickets
    items, total = await list_tickets(db=db_session, shop_id=shop.id, search="   ")
    assert total == 2
    assert len(items) == 2


@pytest.mark.asyncio
async def test_ticket_search_sanitization_padded_and_uuid(db_session):
    shop, _ = await _seed_common(db_session)
    customer = Customer(
        shop_id=shop.id,
        full_name="Maria Lopez",
        phone_number="0992222222",
        email="maria@example.com",
    )
    db_session.add(customer)
    await db_session.flush()

    t1 = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        device_brand="Samsung",
        device_model="Galaxy S23",
        issue_description="Puerto de carga sulfatado",
        status=TicketStatusEnum.EN_REVISION,
    )
    db_session.add(t1)
    await db_session.flush()

    # Padded brand search
    items, total = await list_tickets(db=db_session, shop_id=shop.id, search="  Samsung  ")
    assert total == 1
    assert items[0].id == t1.id

    # Padded UUID search
    items_uuid, total_uuid = await list_tickets(db=db_session, shop_id=shop.id, search=f"  {t1.id}  ")
    assert total_uuid == 1
    assert items_uuid[0].id == t1.id


@pytest.mark.asyncio
async def test_client_search_sanitization(db_session):
    shop, _ = await _seed_common(db_session)
    c1 = Customer(
        shop_id=shop.id,
        full_name="Carlos Santana",
        phone_number="0993333333",
        email="carlos@example.com",
    )
    c2 = Customer(
        shop_id=shop.id,
        full_name="Ana Torres",
        phone_number="0994444444",
        email="ana@example.com",
    )
    db_session.add_all([c1, c2])
    await db_session.flush()

    service = ClientService(db_session)

    # Whitespace-only search should return all clients
    items, total = await service.get_clients(shop_id=shop.id, search="   ")
    assert total == 2

    # Padded name search should match Carlos
    items_carlos, total_carlos = await service.get_clients(shop_id=shop.id, search="  Carlos  ")
    assert total_carlos == 1
    assert items_carlos[0].id == c1.id


@pytest.mark.asyncio
async def test_inventory_search_sanitization(db_session):
    shop, user = await _seed_common(db_session)
    i1 = Inventory(
        shop_id=shop.id,
        item_name="Display Samsung A12",
        sku="DSP-A12",
        stock_quantity=5,
        cost_price=Decimal("15.00"),
        selling_price=Decimal("35.00"),
        low_stock_alert=2,
        is_active=True,
    )
    i2 = Inventory(
        shop_id=shop.id,
        item_name="Bateria iPhone 11",
        sku="BAT-IP11",
        stock_quantity=10,
        cost_price=Decimal("12.00"),
        selling_price=Decimal("30.00"),
        low_stock_alert=3,
        is_active=True,
    )
    db_session.add_all([i1, i2])
    await db_session.flush()

    # Whitespace-only search and sku should return all active items
    res_ws = await list_inventory(
        search="   ",
        sku="   ",
        skip=0,
        limit=50,
        current_user=user,
        db=db_session,
    )
    assert res_ws.total == 2

    # Padded search should match Display
    res_search = await list_inventory(
        search="  Display Samsung  ",
        sku=None,
        skip=0,
        limit=50,
        current_user=user,
        db=db_session,
    )
    assert res_search.total == 1
    assert res_search.items[0].id == i1.id

    # Padded sku should match Battery
    res_sku = await list_inventory(
        search=None,
        sku="  BAT-IP11  ",
        skip=0,
        limit=50,
        current_user=user,
        db=db_session,
    )
    assert res_sku.total == 1
    assert res_sku.items[0].id == i2.id
