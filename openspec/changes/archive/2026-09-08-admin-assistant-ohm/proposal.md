# Change Proposal: Ohm Administrative Assistant (Shop-Level Analytics & Inquiries)

## 1. Context & Motivation
Workshop administrators currently need to inspect dashboard widgets, filter tables, or open separate modal views to understand their daily operational performance (revenue collected, volume of newly checked-in devices, and stagnant tickets requiring attention). 

Introducing Ohm to the administrator panel as a conversational "spoken dashboard" allows shop owners to obtain quick, accurate operational metrics on demand. Instead of allowing arbitrary text-to-SQL generation (which introduces security risks, SQL injection vectors, and multi-tenant leakage), this design uses a **closed intent catalog** with deterministic SQL execution and lightweight natural language formatting.

## 2. Proposed Solution
1. **Closed Intent Catalog (v1)**:
   - `ganancias_del_dia`: Sum of `total_cost` for tickets delivered/completed today (`status == 'LISTO_PARA_RETIRAR'` with update/delivery timestamp today).
   - `equipos_ingresados_hoy`: Count of tickets created today (`created_at >= start_of_today`).
   - `equipos_sin_tocar`: Active tickets (`EN_ESPERA_INGRESO`, `EN_REVISION`, `ESPERANDO_APROBACION`, `ESPERANDO_REPUESTO`, `EN_REPARACION`) without status updates for more than 48 hours.
2. **Intent Classification & Safe Execution**:
   - `POST /admin/assistant/query` receives `{ message: str }`, guarded by `admin_guard`.
   - The query is classified by `gemini-3.5-flash-lite` against the closed catalog (or mapped directly from pre-defined chip shortcuts).
   - If classified to an intent, the server runs a deterministic, tenant-isolated SQLAlchemy query (`where(Ticket.shop_id == shop_id)`).
   - The fast model summarizes the verified numerical results into a warm, concise conversational response.
   - If unclassified (`NONE`), a canned fallback response lists supported capabilities without querying the database or invoking heavy reasoning models.
3. **Stateless Conversational UX**:
   - In accordance with architectural alignment, v1 is **stateless**: each interaction is self-contained and held only in client component state while the drawer is open. No database tables or schema migrations are required.
4. **Frontend Reuse**:
   - Reuse `AiChatBubble` and `AiChatDrawer` in `AdminDashboard.jsx` using `context="admin"`.
   - Render 3 quick-action chips above the input: "💰 Ganancias de hoy", "📥 Equipos ingresados hoy", "⏱️ Equipos sin tocar".
   - Hide ticket-specific RAG/diagnostic feedback controls in admin mode.

## 3. Impact & Scope
- **Backend**: New router `app/routers/admin_assistant.py`, service `app/services/admin_assistant_service.py`, registered in `app/main.py`.
- **Frontend**: `AiChatDrawer.jsx` handles `context="admin"`, renders admin chips, dispatches to `/admin/assistant/query`. Mount `AiChatBubble` in `AdminDashboard.jsx`.
- **Security**: Multi-tenant isolation enforced via `admin_guard` and `shop_id` scoping in all SQL operations.
