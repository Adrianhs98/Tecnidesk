# Tasks: Allow Technician Device Intake (Per-Shop Flag)

## 1. Database Schema & Migration
- [x] 1.1 Update `Shop` model in `backend/app/models/shop.py` to add `allow_technician_intake: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa.text("false"), default=False)`
- [x] 1.2 Create Alembic migration `backend/alembic/versions/f6a7b8c9d0e1_add_allow_technician_intake_to_shops.py` revising `e5f6a7b8c9d0`
- [x] 1.3 Add Pydantic schemas in `backend/app/schemas/shop.py`: `ShopSettingsUpdate` and `ShopSettingsResponse`
- [x] 1.4 Update `TechnicianMeResponse` schema in `backend/app/schemas/technician.py` to include `allow_technician_intake: bool = False`

## 2. Backend Implementation (TDD)
- [x] 2.1 Implement `verify_can_create_ticket` dependency in `backend/app/core/dependencies.py`
- [x] 2.2 Wire `verify_can_create_ticket` into `POST /tickets` in `backend/app/routers/tickets.py`
- [x] 2.3 Implement `get_shop_settings` and `update_shop_settings` in `backend/app/services/shop_service.py`
- [x] 2.4 Add `GET /shops/settings` and `PATCH /shops/settings` in `backend/app/routers/shops.py`
- [x] 2.5 Update `get_technician_me` in `backend/app/services/technician_service.py` to resolve and return `allow_technician_intake`
- [x] 2.6 Create unit tests in `backend/tests/unit/test_technician_intake.py` covering:
  - Admin creates ticket (regardless of flag) -> 201
  - Technician creates ticket with flag = False -> 403 Forbidden
  - Technician creates ticket with flag = True -> 201 Created
  - GET /shops/settings returns flag value
  - PATCH /shops/settings updates flag (admin only)
  - PATCH /shops/settings rejects technician -> 403 Forbidden
  - GET /technicians/me includes allow_technician_intake
- [x] 2.7 Verify all backend unit tests pass (GREEN)

## 3. Frontend Implementation & Tests
- [x] 3.1 Add `fetchShopSettings` and `updateShopSettings` to `frontend/src/api/shop.js`
- [x] 3.2 Add "Permitir ingreso de equipos a técnicos" toggle in `frontend/src/features/admin/components/SlaSettingsModal.jsx`
- [x] 3.3 Add "Ingresar Equipo" action button and modal mount in `frontend/src/features/technician/TechnicianDashboard.jsx` guarded by `techProfile?.allow_technician_intake`
- [x] 3.4 Add unit tests in `frontend/src/tests/features/admin/SlaSettingsModal.test.jsx` for settings toggle
- [x] 3.5 Add unit tests in `frontend/src/tests/features/TechnicianPortal.test.jsx` for intake button rendering based on flag
- [x] 3.6 Verify full frontend test suite passes with `npx vitest run`

## 4. Verification & Archival
- [x] 4.1 Run full regression suites (backend + frontend)
- [x] 4.2 Move change to `openspec/changes/archive/` and record permanent spec in `openspec/specs/`
