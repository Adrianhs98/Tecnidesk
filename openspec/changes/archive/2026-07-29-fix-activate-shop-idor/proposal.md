# Proposal: fix-activate-shop-idor

**Status**: proposed  
**Date**: 2026-07-29  
**Author**: SDD Onboarding  

---

## Problem

`POST /tickets/admin/activate-shop` uses `get_current_user` as its only guard.
Any authenticated user from any tenant can call this endpoint with an arbitrary
`shop_id` and extend or reactivate that shop's subscription without restriction.

This is an **IDOR (Insecure Direct Object Reference)** vulnerability: the
resource identifier (`shop_id`) is user-controlled and the authorization check
does not verify the caller has permission to act on that resource.

### Root Cause

`get_current_user` only validates that the JWT is well-formed and the user exists.
It does not check:
- whether the caller owns or manages the target `shop_id`
- whether the caller has any platform-level (SaaS operator) privilege

The existing `admin_guard` and `subscription_guard` are scoped to a single tenant
and cannot serve as platform guards.

### Impact

| Risk | Severity |
|---|---|
| Any tenant user can activate any other tenant's subscription for free | CRITICAL |
| Any tenant user can extend any subscription by up to N days | CRITICAL |
| No audit trail distinguishes legitimate activations from exploits | HIGH |

---

## Proposed Solution

Protect the endpoint with a **platform-level API Key** (`SUPERADMIN_API_KEY`)
read from environment variables, completely independent of the tenant
authentication system.

**Rationale for API Key over role-based approach:**

- No `superadmin` role or platform-level user concept exists in the current data
  model. Adding one would require a database migration and significant auth
  refactoring — out of scope and high risk.
- The endpoint is an operator tool (activated by the SaaS owner via scripts or
  internal tooling), not a user-facing feature. API Key is the appropriate
  pattern for machine-to-machine / operator access.
- A static secret managed via environment variable (Render secret env var) is
  consistent with how other secrets (`FERNET_KEY`, `JWT_SECRET`) are managed in
  this project.

**Mechanism:**

1. Add `SUPERADMIN_API_KEY` to `Settings` in `app/config.py`.
2. Create a FastAPI dependency `superadmin_key_guard` in `app/core/dependencies.py`
   that reads the `X-Superadmin-Key` request header and compares it via
   `secrets.compare_digest` (constant-time, no timing attacks).
3. Replace `Depends(get_current_user)` on `activate_shop` with
   `Depends(superadmin_key_guard)` — remove all tenant JWT logic from this
   endpoint.
4. Add the env var to `.env.example` with a placeholder value.

---

## Capabilities Affected

| Capability | Status |
|---|---|
| `platform-admin/activate-shop` | new |

---

## Files to Change

| File | Change |
|---|---|
| `backend/app/config.py` | Add `superadmin_api_key: str` field to `Settings` |
| `backend/app/core/dependencies.py` | Add `superadmin_key_guard` dependency |
| `backend/app/routers/tickets.py` | Swap guard on `activate_shop` |
| `backend/app/.env.example` | Document new env var (create if missing) |

---

## Out of Scope

- Audit logging for activations (separate concern)
- Rate limiting on this endpoint (low priority, key is already a secret)
- Role-based superadmin system (future, requires migration)
- Any changes to tenant auth flows

---

## Acceptance Criteria

1. `POST /tickets/admin/activate-shop` without `X-Superadmin-Key` header returns `HTTP 401`.
2. `POST /tickets/admin/activate-shop` with a wrong key returns `HTTP 403`.
3. `POST /tickets/admin/activate-shop` with the correct key successfully activates the shop.
4. A valid tenant JWT **without** the correct key is rejected (JWT alone is not sufficient).
5. The comparison uses `secrets.compare_digest` (no timing leak).
6. `SUPERADMIN_API_KEY` is sourced from `Settings` (env var), never hardcoded.
