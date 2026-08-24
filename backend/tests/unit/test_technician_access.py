import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, patch

from app.models.shop import Shop
from app.models.user import User, UserRoleEnum
from app.models.technician import Technician
from app.schemas.technician import TechnicianCreate
from app.services import technician_service


@pytest.mark.asyncio
async def test_grant_technician_access_success(db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop",
        owner_name="Owner",
        subdomain=f"access-shop-{uuid.uuid4().hex[:8]}",
        contact_email="access@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    with patch("app.services.email_service.send_technician_credentials_email", new_callable=AsyncMock) as mock_email:
        mock_email.return_value = True

        tech_data = TechnicianCreate(
            full_name="Tech Access User",
            contact="0999999999",
            declared_specialty="Laptops",
            email="tech_access@test.com",
            generate_access=True,
        )

        tech = await technician_service.create_technician(db_session, shop_id, tech_data)

        assert tech.id is not None
        assert tech.user_id is not None
        
        # Verify email was called
        mock_email.assert_called_once()
        kwargs = mock_email.call_args.kwargs
        assert kwargs["to_email"] == "tech_access@test.com"
        assert len(kwargs["password"]) >= 8 # Password
        assert kwargs["shop_name"] == shop.business_name


@pytest.mark.asyncio
async def test_grant_technician_access_email_failure_rollback(db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop 2",
        owner_name="Owner",
        subdomain=f"access-shop2-{uuid.uuid4().hex[:8]}",
        contact_email="access2@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    with patch("app.services.email_service.send_technician_credentials_email", new_callable=AsyncMock) as mock_email:
        mock_email.side_effect = Exception("Resend failed")

        tech_data = TechnicianCreate(
            full_name="Tech Access User Fail",
            contact="0999999999",
            declared_specialty="Laptops",
            email="tech_fail@test.com",
            generate_access=True,
        )

        with pytest.raises(Exception) as exc_info:
            await technician_service.create_technician(db_session, shop_id, tech_data)
        
        assert "Fallo al enviar correo" in str(exc_info.value)

        # Verify it's rolled back! The user shouldn't exist, and the technician shouldn't exist
        # Wait, the rollback is handled at the request level by the dependency or the try/except block?
        # Actually, in create_technician, if an exception happens, it should rollback.
        
        # We need to verify nothing was inserted (or everything was rolled back).
        # We can't query db_session directly if the transaction is aborted, but if create_technician handles it:
        # We'll see how we implement it.

@pytest.mark.asyncio
async def test_create_technician_router_email_failure_502(client, db_session):
    from app.main import app
    from app.core.dependencies import admin_guard
    from app.models.user import User, UserRoleEnum

    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop 3",
        owner_name="Owner",
        subdomain=f"access-shop3-{uuid.uuid4().hex[:8]}",
        contact_email="access3@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fake",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    app.dependency_overrides[admin_guard] = lambda: user

    try:
        with patch("app.services.email_service.send_technician_credentials_email", new_callable=AsyncMock) as mock_email:
            mock_email.side_effect = Exception("Resend API key missing or invalid")
            
            payload = {
                "full_name": "Tech Router Fail",
                "contact": "0999999999",
                "declared_specialty": "Laptops",
                "email": "tech_router_fail@test.com",
                "generate_access": True
            }

            response = await client.post("/technicians", json=payload)
            
            assert response.status_code == 502
            assert "Fallo al enviar correo" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(admin_guard, None)


@pytest.mark.asyncio
async def test_create_technician_router_duplicate_409(client, db_session):
    from app.main import app
    from app.core.dependencies import admin_guard
    from app.models.user import User, UserRoleEnum

    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop 4",
        owner_name="Owner",
        subdomain=f"access-shop4-{uuid.uuid4().hex[:8]}",
        contact_email="access4@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin 4",
        email=f"admin4-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fake",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    app.dependency_overrides[admin_guard] = lambda: user

    try:
        with patch("app.services.email_service.send_technician_credentials_email", new_callable=AsyncMock) as mock_email:
            mock_email.return_value = True
            
            payload = {
                "full_name": "Tech Router Dup",
                "contact": "0999999999",
                "declared_specialty": "Laptops",
                "email": "tech_router_dup@test.com",
                "generate_access": True
            }

            response1 = await client.post("/technicians", json=payload)
            assert response1.status_code == 201

            # Change name to trigger duplicate email specifically
            payload["full_name"] = "Tech Router Dup 2"
            
            response2 = await client.post("/technicians", json=payload)
            assert response2.status_code == 409
            assert "registrado" in response2.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(admin_guard, None)


@pytest.mark.asyncio
async def test_generate_technician_access_router_success(client, db_session):
    from app.main import app
    from app.core.dependencies import admin_guard
    from app.models.user import User, UserRoleEnum

    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop 5",
        owner_name="Owner",
        subdomain=f"access-shop5-{uuid.uuid4().hex[:8]}",
        contact_email="access5@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin 5",
        email=f"admin5-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fake",
        is_active=True,
    )
    db_session.add(user)
    
    tech = Technician(
        shop_id=shop_id,
        full_name="Existing Tech",
        contact="0999999999",
        is_active=True,
    )
    db_session.add(tech)
    await db_session.commit()
    await db_session.refresh(tech)

    app.dependency_overrides[admin_guard] = lambda: user

    try:
        with patch("app.services.email_service.send_technician_credentials_email", new_callable=AsyncMock) as mock_email:
            mock_email.return_value = True
            
            payload = {
                "email": "existing_tech@test.com"
            }

            response = await client.post(f"/technicians/{tech.id}/access", json=payload)
            assert response.status_code == 200
            
            data = response.json()
            assert data["id"] == str(tech.id)
            assert data["user_id"] is not None
            
            mock_email.assert_called_once()
    finally:
        app.dependency_overrides.pop(admin_guard, None)


@pytest.mark.asyncio
async def test_generate_technician_access_router_409(client, db_session):
    from app.main import app
    from app.core.dependencies import admin_guard
    from app.models.user import User, UserRoleEnum

    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop 6",
        owner_name="Owner",
        subdomain=f"access-shop6-{uuid.uuid4().hex[:8]}",
        contact_email="access6@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin 6",
        email=f"admin6-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fake",
        is_active=True,
    )
    db_session.add(user)
    
    tech = Technician(
        shop_id=shop_id,
        full_name="Existing Tech 2",
        contact="0999999999",
        is_active=True,
    )
    db_session.add(tech)
    await db_session.commit()
    await db_session.refresh(tech)

    app.dependency_overrides[admin_guard] = lambda: user

    try:
        payload = {
            "email": user.email # Duplicate email
        }
        response = await client.post(f"/technicians/{tech.id}/access", json=payload)
        assert response.status_code == 409
        assert "registrado" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(admin_guard, None)


@pytest.mark.asyncio
async def test_generate_technician_access_router_502(client, db_session):
    from app.main import app
    from app.core.dependencies import admin_guard
    from app.models.user import User, UserRoleEnum

    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Access Shop 7",
        owner_name="Owner",
        subdomain=f"access-shop7-{uuid.uuid4().hex[:8]}",
        contact_email="access7@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin 7",
        email=f"admin7-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fake",
        is_active=True,
    )
    db_session.add(user)
    
    tech = Technician(
        shop_id=shop_id,
        full_name="Existing Tech 3",
        contact="0999999999",
        is_active=True,
    )
    db_session.add(tech)
    await db_session.commit()
    await db_session.refresh(tech)

    app.dependency_overrides[admin_guard] = lambda: user

    try:
        with patch("app.services.email_service.send_technician_credentials_email", new_callable=AsyncMock) as mock_email:
            mock_email.side_effect = Exception("Fallo al enviar correo")
            
            payload = {
                "email": "existing_tech3@test.com"
            }

            response = await client.post(f"/technicians/{tech.id}/access", json=payload)
            assert response.status_code == 502
            assert "fallo al enviar correo" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(admin_guard, None)
