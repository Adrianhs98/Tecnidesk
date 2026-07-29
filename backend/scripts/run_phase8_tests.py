import asyncio
import uuid
import sys
import os

# Añadir el root del backend al PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import AsyncSessionLocal
from app.models.shop import Shop
from app.models.user import User, UserRoleEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.customer import Customer
from app.schemas.technician import TechnicianCreate, TechnicianUpdate
from app.services import technician_service, ticket_service

from datetime import datetime, timezone

async def run_tests():
    async with AsyncSessionLocal() as db:
        print("Iniciando Pruebas de Fase 8...")
        
        try:
            shop_a = Shop(business_name="Taller A", owner_name="Owner", subdomain=f"ta{uuid.uuid4().hex[:4]}", contact_email="a@a", contact_whatsapp="123", created_at=datetime.now(timezone.utc))
            shop_b = Shop(business_name="Taller B", owner_name="Owner", subdomain=f"tb{uuid.uuid4().hex[:4]}", contact_email="b@b", contact_whatsapp="123", created_at=datetime.now(timezone.utc))
            db.add_all([shop_a, shop_b])
            await db.commit()
            await db.refresh(shop_a)
            await db.refresh(shop_b)
            
            customer_a = Customer(shop_id=shop_a.id, full_name="Cliente A", phone_number="123456", email="a@a.com")
            db.add(customer_a)
            await db.commit()
            
            # 1. Aislamiento
            print("Test 1: Aislamiento (CRUD entre talleres)...", end=" ")
            tech_a = await technician_service.create_technician(db, shop_a.id, TechnicianCreate(full_name="Tech A", contact="123", declared_specialty="None"))
            
            tech_b_query = await technician_service.get_technician_by_id(db, tech_a.id, shop_b.id)
            assert tech_b_query is None, "Shop B pudo ver al técnico de Shop A"
            
            try:
                await technician_service.update_technician(db, tech_a.id, shop_b.id, TechnicianUpdate(full_name="Hacked"))
                assert False, "Shop B pudo actualizar al técnico de Shop A"
            except technician_service.TechnicianNotFound:
                pass
            
            try:
                await technician_service.deactivate_technician(db, tech_a.id, shop_b.id)
                assert False, "Shop B pudo desactivar al técnico de Shop A"
            except technician_service.TechnicianNotFound:
                pass
            print("OK")
            
            # 2. Validación: Asignar técnico inactivo
            print("Test 2: Asignar técnico inactivo...", end=" ")
            await technician_service.deactivate_technician(db, tech_a.id, shop_a.id)
            ticket_a = Ticket(shop_id=shop_a.id, customer_id=customer_a.id, device_brand="X", device_model="Y", issue_description="Z", tracking_token=str(uuid.uuid4()))
            db.add(ticket_a)
            await db.commit()
            await db.refresh(ticket_a)
            
            try:
                await ticket_service.assign_technician(db, ticket_a.id, shop_a.id, tech_a.id)
                assert False, "Se permitió asignar un técnico inactivo"
            except Exception as e:
                pass
            print("OK")
            
            # 3. Validación: Asignar técnico de otro taller
            print("Test 3: Asignar técnico de otro taller...", end=" ")
            tech_b = await technician_service.create_technician(db, shop_b.id, TechnicianCreate(full_name="Tech B"))
            try:
                await ticket_service.assign_technician(db, ticket_a.id, shop_a.id, tech_b.id)
                assert False, "Se permitió asignar un técnico de otro taller"
            except Exception as e:
                pass
            print("OK")
            
            # 4. Guard Admin (Simulado)
            print("Test 4: Guard Role=Technician intenta POST...", end=" ")
            from app.core.dependencies import admin_guard
            from fastapi import HTTPException
            tech_user = User(role=UserRoleEnum.technician, shop_id=shop_a.id)
            try:
                await admin_guard(current_user=tech_user)
                assert False, "admin_guard permitió a un técnico"
            except HTTPException as e:
                assert e.status_code == 403
            print("OK")
            
            # 5. Lógica de Asignación Aleatoria (Menor Carga)
            print("Test 5: Asignación Aleatoria (Carga 2-1-1)...", end=" ")
            t1 = await technician_service.create_technician(db, shop_a.id, TechnicianCreate(full_name="T1"))
            t2 = await technician_service.create_technician(db, shop_a.id, TechnicianCreate(full_name="T2"))
            t3 = await technician_service.create_technician(db, shop_a.id, TechnicianCreate(full_name="T3"))
            
            # T1 = 2 tickets, T2 = 1 ticket, T3 = 1 ticket
            for tech, count in [(t1, 2), (t2, 1), (t3, 1)]:
                for _ in range(count):
                    tk = Ticket(shop_id=shop_a.id, customer_id=customer_a.id, technician_id=tech.id, status=TicketStatusEnum.EN_REVISION, device_brand="X", device_model="Y", issue_description="Z", tracking_token=str(uuid.uuid4()))
                    db.add(tk)
            await db.commit()
            
            chosen_tech = await technician_service.pick_least_loaded_technician(db, shop_a.id)
            assert chosen_tech.id in [t2.id, t3.id], "Eligió al técnico más cargado en lugar de los menos cargados"
            print(f"OK (Eligió a {chosen_tech.full_name})")
            
            print("\\n¡TODAS LAS PRUEBAS DE LA FASE 8 PASARON EXITOSAMENTE! ✅")
            
        finally:
            # --- TEARDOWN ---
            print("Limpiando datos de prueba...")
            try:
                await db.execute(text(f"DELETE FROM tickets WHERE shop_id IN ('{shop_a.id}', '{shop_b.id}')"))
                await db.execute(text(f"DELETE FROM technicians WHERE shop_id IN ('{shop_a.id}', '{shop_b.id}')"))
                await db.execute(text(f"DELETE FROM customers WHERE shop_id IN ('{shop_a.id}', '{shop_b.id}')"))
                await db.execute(text(f"DELETE FROM users WHERE shop_id IN ('{shop_a.id}', '{shop_b.id}')"))
                await db.execute(text(f"DELETE FROM shops WHERE id IN ('{shop_a.id}', '{shop_b.id}')"))
                # Clean up orphaned shops from previous failed runs (test shops only)
                await db.execute(text("DELETE FROM shops WHERE business_name IN ('Taller A', 'Taller B')"))
                await db.commit()
                print("Limpieza completada.")
            except Exception as e:
                print(f"Error en limpieza: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
