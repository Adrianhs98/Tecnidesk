import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from app.models.diagnostic import DiagnosticConversation
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.models.user import User, UserRoleEnum
from app.core.security import create_access_token

class MockResponse:
    text = "Respuesta mockeada del copiloto."

class MockModels:
    async def generate_content(self, *args, **kwargs):
        return MockResponse()

class MockAio:
    def __init__(self):
        self.models = MockModels()

class MockClient:
    def __init__(self, *args, **kwargs):
        self.aio = MockAio()

@pytest.mark.asyncio
async def test_diagnostic_chat_saves_correct_technician_id(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """
    Verifica que al iniciar un chat de diagnóstico, la conversación
    guarde el Technician.id real y NO el User.id del token (current_user.id).
    """
    monkeypatch.setattr("app.services.correction_service.genai.Client", MockClient)

    from app.models.shop import Shop
    from app.models.customer import Customer
    import uuid

    # 1. Crear Taller y Usuario Técnico
    shop_id = uuid.uuid4()
    from datetime import datetime, timezone
    shop = Shop(id=shop_id, business_name="Test Shop", owner_name="Owner Test", subdomain=f"test-{shop_id.hex[:6]}", contact_email="shop@test.com", contact_whatsapp="123", created_at=datetime.now(timezone.utc), subscription_status="active")
    db_session.add(shop)
    await db_session.commit()


    user = User(
        email="tech_chat_router@test.com",
        password_hash="hashed",
        full_name="Tech Router",
        shop_id=shop_id,
        role=UserRoleEnum.technician,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Crear el Perfil de Técnico vinculado al Usuario
    tech = Technician(
        user_id=user.id,
        shop_id=shop_id,
        full_name="Técnico Chat Router",
        contact="123456789",
    )
    db_session.add(tech)
    await db_session.commit()
    await db_session.refresh(tech)

    # Crear Customer
    customer = Customer(shop_id=shop_id, full_name="Test Customer", phone_number="593999999999", email="test@test.com")
    db_session.add(customer)
    await db_session.commit()
    await db_session.refresh(customer)

    # 3. Crear un Ticket asignado a ese Técnico
    ticket = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Test issue",
        status="EN_REVISION",
        technician_id=tech.id,
    )
    db_session.add(ticket)
    await db_session.commit()
    await db_session.refresh(ticket)

    # 4. Autenticar como el Usuario
    token = create_access_token(user_id=str(user.id), shop_id=str(shop_id), role="technician")

    # Dependency override para evitar el checkeo de Subscription y 402
    from app.core.dependencies import subscription_guard
    from app.main import app
    app.dependency_overrides[subscription_guard] = lambda: user
    
    try:
        # 5. Disparar el POST al Chat de Diagnóstico
        payload = {"message": "La pantalla no enciende tras golpe"}
        response = await client.post(
            f"/tickets/{ticket.id}/diagnostic-chat",
            json=payload,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Error en endpoint: {response.text}"
    finally:
        app.dependency_overrides.pop(subscription_guard, None)
    
    # 6. Verificar en la base de datos
    result = await db_session.execute(
        select(DiagnosticConversation)
        .where(DiagnosticConversation.ticket_id == ticket.id)
    )
    conv = result.scalars().first()
    
    assert conv is not None
    # EL FIX: Debe guardar el id del TÉCNICO, NO del USUARIO
    assert conv.technician_id == tech.id, f"technician_id={conv.technician_id} (esperaba tech.id={tech.id})"
    assert conv.technician_id != user.id, "Guardó el user_id en lugar del technician_id"
    assert conv.technician_id == tech.id, "El technician_id guardado no coincide con el del perfil de Técnico"
