import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.core.dependencies import verify_can_create_ticket
from app.models.shop import Shop
from app.models.user import User, UserRoleEnum
from app.models.technician import Technician
from app.schemas.shop import ShopSettingsUpdate, ShopSettingsResponse
from app.schemas.technician import TechnicianMeResponse
from app.services import shop_service, ticket_service, technician_service
from app.routers.shops import get_shop_settings_endpoint, update_shop_settings_endpoint


@pytest.mark.asyncio
async def test_verify_can_create_ticket_admin_allowed():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    admin_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        is_active=True,
    )

    # Admin is allowed regardless of shop flag
    result = await verify_can_create_ticket(current_user=admin_user, db=db)
    assert result == admin_user
    # db.get shouldn't even be called for admin
    db.get.assert_not_called()


@pytest.mark.asyncio
async def test_verify_can_create_ticket_technician_denied_when_flag_false():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    tech_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        is_active=True,
    )
    shop = Shop(
        id=shop_id,
        business_name="Test Shop",
        owner_name="Owner",
        subdomain="test-shop",
        contact_email="test@shop.com",
        contact_whatsapp="593991234567",
        allow_technician_intake=False,
    )
    db.get.return_value = shop

    with pytest.raises(HTTPException) as exc_info:
        await verify_can_create_ticket(current_user=tech_user, db=db)

    assert exc_info.value.status_code == 403
    assert "No tienes permiso para ingresar equipos" in exc_info.value.detail
    db.get.assert_called_once_with(Shop, shop_id)


@pytest.mark.asyncio
async def test_verify_can_create_ticket_technician_allowed_when_flag_true():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    tech_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        is_active=True,
    )
    shop = Shop(
        id=shop_id,
        business_name="Test Shop",
        owner_name="Owner",
        subdomain="test-shop",
        contact_email="test@shop.com",
        contact_whatsapp="593991234567",
        allow_technician_intake=True,
    )
    db.get.return_value = shop

    result = await verify_can_create_ticket(current_user=tech_user, db=db)
    assert result == tech_user
    db.get.assert_called_once_with(Shop, shop_id)


@pytest.mark.asyncio
async def test_verify_can_create_ticket_unknown_role_denied():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    unknown_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role="other_role",
        is_active=True,
    )

    with pytest.raises(HTTPException) as exc_info:
        await verify_can_create_ticket(current_user=unknown_user, db=db)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_shop_service_get_and_update_settings():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Test Shop",
        owner_name="Owner",
        subdomain="test-shop",
        contact_email="test@shop.com",
        contact_whatsapp="593991234567",
        allow_technician_intake=False,
    )

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = shop
    db.execute.return_value = result_mock

    # Get settings
    settings = await shop_service.get_shop_settings(db, shop_id)
    assert settings["allow_technician_intake"] is False

    # Update settings
    updated = await shop_service.update_shop_settings(db, shop_id, allow_technician_intake=True)
    assert updated["allow_technician_intake"] is True
    assert shop.allow_technician_intake is True
    db.add.assert_called_with(shop)
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_shops_settings_endpoints():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    admin_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        is_active=True,
    )

    with patch("app.routers.shops.get_shop_settings", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"allow_technician_intake": True}
        res = await get_shop_settings_endpoint(current_user=admin_user, db=db)
        assert isinstance(res, ShopSettingsResponse)
        assert res.allow_technician_intake is True
        mock_get.assert_called_once_with(db, shop_id)

    with patch("app.routers.shops.update_shop_settings", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = {"allow_technician_intake": True}
        payload = ShopSettingsUpdate(allow_technician_intake=True)
        res = await update_shop_settings_endpoint(payload=payload, current_user=admin_user, db=db)
        assert isinstance(res, ShopSettingsResponse)
        assert res.allow_technician_intake is True
        mock_update.assert_called_once_with(db, shop_id, True)


@pytest.mark.asyncio
async def test_technician_me_response_includes_allow_technician_intake():
    db = AsyncMock()
    shop_id = uuid.uuid4()
    user_id = uuid.uuid4()
    tech_id = uuid.uuid4()

    user = User(
        id=user_id,
        shop_id=shop_id,
        full_name="Tech Specialist",
        email="tech@shop.com",
        role=UserRoleEnum.technician,
        is_active=True,
    )
    tech = Technician(
        id=tech_id,
        shop_id=shop_id,
        user_id=user_id,
        full_name="Tech Specialist",
        declared_specialty="Microelectrónica",
        is_active=True,
    )

    # 1. Tech lookup mock
    tech_result = MagicMock()
    tech_result.scalar_one_or_none.return_value = tech

    # 2. Tickets lookup mock
    tickets_result = MagicMock()
    tickets_result.scalars.return_value.all.return_value = []

    db.execute.side_effect = [tech_result, tickets_result]
    db.scalar.return_value = True  # Shop.allow_technician_intake

    me = await technician_service.get_technician_me(db, user, shop_id)
    assert isinstance(me, TechnicianMeResponse)
    assert me.allow_technician_intake is True
