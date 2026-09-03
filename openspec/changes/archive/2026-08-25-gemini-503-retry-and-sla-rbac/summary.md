# SDD Archive: 2026-08-25 Gemini 503 Retry & SLA Config RBAC

## 1. Summary of Changes
- **Fix SLA Config RBAC (403):** Migrated `GET /shops/sla-config` dependency from `admin_guard` to `subscription_guard` to allow workshop technicians to fetch SLA thresholds used for stale badge calculations in `TechnicianDashboard.jsx`. Preserved strict `admin_guard` on `PATCH /shops/sla-config`.
- **Automatic Retries for Gemini 503:** Implemented exponential backoff retries (3 attempts: 1s, 2s, 4s) in `CorrectionService` and `ExplanationService` when encountering `ServerError` (503 Service Unavailable) from Google Gemini SDK, with graceful fallback.
- **Dynamic Frontend Feedback:** Implemented a timer in `AiChatDrawer.jsx` that smoothly switches loading status to `"Ohm está experimentando alta demanda, reintentando conexión..."` with warm amber styling (`.ai-thinking-bubble.retrying`) if requests take more than 3.5s.
- **Assistant Rebranding:** Fully unified technical assistant naming to **Ohm** across frontend and backend.

## 2. Verification
- Backend Pytest: 146 passed (100%)
- Frontend Vitest: 97 passed (100%)
