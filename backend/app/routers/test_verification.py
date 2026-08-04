import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.user import User, UserRoleEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_item import TicketItem, ItemTypeEnum
from app.models.subscription import SubscriptionStatusEnum
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

import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/dev-test-e2e", tags=["Test"])

@router.post("/run")
async def run_e2e_tests(db: AsyncSession = Depends(get_db)):
    results = []
    def log(msg):
        results.append(msg)
        logging.info(msg)

    try:
        log("--- INICIANDO VERIFICACIÓN END-TO-END TICKET SERVICE ---")
        
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
        await db.commit()
        await db.refresh(shop1)
        await db.refresh(shop2)

        customer1 = Customer(
            shop_id=shop1.id, full_name="Cliente Test 1",
            phone_number="593999999999", email="cliente1@mail.com"
        )
        db.add(customer1)
        
        tech1 = User(
            shop_id=shop1.id, email=f"tech_{rand1}@test.com",
            password_hash="fake", full_name="Technician 1",
            role=UserRoleEnum.technician, is_active=True,
        )
        db.add(tech1)
        await db.commit()
        
        log(f"✅ Datos Seed Creados: Shop1={shop1.id}, Shop2={shop2.id}")

        log("\n--- TEST 1: create_ticket param testing y pin sanitization ---")
        ticket_data = TicketCreate(
            customer_id=customer1.id, device_brand="Samsung", device_model="S22",
            issue_description="Pantalla Rota", pin_or_password="1234",
            diagnostic_notes="Prueba diagnostico", requires_approval=True
        )
        ticket = await create_ticket(db, shop1.id, ticket_data)
        log(f"Ticket Creado ID: {ticket.id}, Tracking: {ticket.tracking_token}")
        
        if getattr(ticket, "pin_or_password", "NO_PIN") is None:
            log("✅ Exito: pin_or_password limpiado.")
        else:
            raise Exception("pin_or_password sigue existiendo")

        log("\n--- TEST 2: Multi-Tenant Query Protection ---")
        # should return empty list for shop2 instead of ticket list
        tickets_s2 = await list_tickets(db, shop2.id)
        if len(tickets_s2) == 0:
            log("✅ Exito: list_tickets en Shop 2 no falla, pero no ve el ticket de shop1.")
        else:
            raise Exception("Shop2 vio tickets ajenos!")
            
        try:
            await get_ticket_by_id(db, ticket.id, shop2.id)
            raise Exception("Pudo leer un ticket ajeno")
        except TicketNotFound:
            log("✅ Exito: Multi-Tenant 404 al intentar leer `get_ticket_by_id` de otro shop_id.")

        try:
            await update_ticket_status(db, ticket.id, shop2.id, TicketStatusEnum.EN_REPARACION)
            raise Exception("Pudo actualizar ticket de shop ajeno")
        except TicketNotFound:
            log("✅ Exito: Multi-Tenant 404 al intentar `update_ticket_status` de otro shop_id.")

        log("\n--- TEST 3: Eager Loading Test (get_ticket_by_id) ---")
        ticket_eager = await get_ticket_by_id(db, ticket.id, shop1.id)
        if getattr(ticket_eager, "pin_or_password", "NO_PIN") is None:
            log("✅ Exito: pin_or_password sanitizado de get_ticket_by_id.")
        else:
            raise Exception("pin omitido de borrar en GET")

        _ = ticket_eager.customer.full_name
        _ = len(ticket_eager.items)
        _ = len(ticket_eager.evidences)
        log("✅ Exito: Relaciones customer, items y evidences estan cargadas (no lazy-load exception).")
            
        log("\n--- TEST 4: Assign Technician ---")
        await assign_technician(db, ticket.id, shop1.id, tech1.id)
        ticket_after_assign = await get_ticket_by_id(db, ticket.id, shop1.id)
        if ticket_after_assign.assigned_technician_id == tech1.id:
            log(f"✅ Exito: Técnico {tech1.id} asignado correctamente.")
        else:
            raise Exception("Error asgnando técnico")
        
        log("\n--- TEST 5: Add Ticket Item y Calculate Total ---")
        item_data = TicketItemCreate(
            item_type=ItemTypeEnum.part,
            description="Pantalla OLED Nueva",
            quantity=1,
            unit_price=Decimal("150.00")
        )
        item = await add_ticket_item(db, ticket.id, shop1.id, item_data)
        log(f"✅ Exito: Item añadido {item.id} - ${item.unit_price} x {item.quantity}")

        ticket_final = await get_ticket_by_id(db, ticket.id, shop1.id)
        if ticket_final.total_cost == Decimal("150.00"):
            log("✅ Exito: El total_cost del ticket se actualizó automáticamente a $150.00.")
        else:
            raise Exception(f"El total_cost esperado 150.00, pero fue {ticket_final.total_cost}")

        log("\n✅ TODAS LAS PRUEBAS PASADAS END-TO-END ✅")
        return {"status": "success", "log": results}

    except Exception as e:
        log(f"❌ ERROR: {e}")
        return {"status": "failed", "log": results}
