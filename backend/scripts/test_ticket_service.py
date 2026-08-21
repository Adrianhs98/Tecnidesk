import uuid
import sys
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select, create_engine
from sqlalchemy.orm import Session, sessionmaker, selectinload

from app.config import get_settings
from app.models.customer import Customer
from app.models.shop import Shop
from app.models.subscription import SubscriptionStatusEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_item import TicketItem, ItemTypeEnum
from app.models.user import User, UserRoleEnum
from app.schemas.ticket import TicketCreate, TicketItemCreate

from app.services.ticket_service import (
    create_ticket,
    get_ticket_by_id,
    list_tickets,
    update_ticket_status,
    assign_technician,
    add_ticket_item,
    TicketNotFound,
)

def get_test_db():
    settings = get_settings()
    # Replace asyncpg with psycopg2 for the testing script to avoid PgBouncer errors
    sync_url = settings.db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    engine = create_engine(sync_url, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return TestingSessionLocal()

# We need a small async wrapper since the service functions are async
import asyncio

async def create_seed_data(db: Session):
    now = datetime.now(timezone.utc)
    rand1 = uuid.uuid4().hex[:6]
    rand2 = uuid.uuid4().hex[:6]
    
    shop1 = Shop(
        business_name=f"Taller {rand1}", owner_name="Owner Admin",
        subdomain=f"sub_{rand1}", contact_email=f"alpha_{rand1}@test.com",
        contact_whatsapp="1234567890", subscription_status=SubscriptionStatusEnum.trial,
        created_at=now,
    )
    shop2 = Shop(
        business_name=f"Taller {rand2}", owner_name="Owner Admin",
        subdomain=f"sub_{rand2}", contact_email=f"beta_{rand2}@test.com",
        contact_whatsapp="0987654321", subscription_status=SubscriptionStatusEnum.trial,
        created_at=now,
    )
    db.add_all([shop1, shop2])
    db.commit()
    db.refresh(shop1)
    db.refresh(shop2)

    customer1 = Customer(
        shop_id=shop1.id, full_name="Cliente Test 1",
        phone_number="593999999999", email="cliente1@mail.com"
    )
    db.add(customer1)
    
    tech1 = User(
        shop_id=shop1.id, email=f"tech_{rand1}@test.com",
        hashed_password="fake", full_name="Technician 1",
        role=UserRoleEnum.technician, is_active=True,
    )
    db.add(tech1)
    db.commit()
    
    return shop1, shop2, customer1, tech1


async def run_tests():
    print("--- INICIANDO VERIFICACIÓN END-TO-END TICKET SERVICE ---")
    
    db = get_test_db()
    # Evitamos drop para no romper otras pruebas, solo creamos nuevos scopes
    shop1, shop2, customer1, tech1 = await create_seed_data(db)
    
    print("\n✅ Datos Seed Creados:")
    print(f"Shop 1: {shop1.id}")
    print(f"Shop 2: {shop2.id}")
    print(f"Customer 1: {customer1.id}")
    print(f"Technician 1: {tech1.id}")

    print("\n--- TEST 1: create_ticket param testing y pin sanitization ---")
    ticket_data = TicketCreate(
        customer_id=customer1.id, device_brand="Samsung", device_model="S22",
        issue_description="Pantalla Rota", pin_or_password="1234",
        diagnostic_notes="Prueba diagnostico", requires_approval=True
    )
    
    # Needs async db mock wrapping if internal funcs use it, but since we use SQLAlchemy 2 we might just
    # test the DB layer by providing a mock async session that throws queries synchronously.
    # ACTUALLY, ticket_service is tightly coupled to AsyncSession. Bypassing PgBouncer with psycopg2 won't work out of the box for ticket_service functions without rewriting them.
    pass

if __name__ == "__main__":
    asyncio.run(run_tests())

if __name__ == "__main__":
    asyncio.run(run_tests())
