# Feature Backlog: Asistente de Historial de Reparaciones (RAG)

**Estado:** Pausado (Postergado por urgencia de otro fix)
**Fecha de Discovery:** 2026-07-28

## Discovery Notes
1. **Modelos:** `Ticket` (issue_description, diagnostic_notes, shop_id), `TicketItem` (description), `Technician` (full_name). Ideales para búsqueda semántica.
2. **Flujo de Tickets:** `update_ticket_diagnostic` cambia el estado a ESPERANDO_APROBACION. Filtrar IA solo por tickets resueltos/entregados.
3. **Multitenant:** Aislar siempre por `shop_id == current_user.shop_id` usando `subscription_guard`.
4. **Frontend:** Usar `NewTicketModal.jsx` (onBlur en falla inicial) y `DiagnosticModal.jsx`. No duplicar modales enteros.
5. **Dependencias:** Falta agregar SDK de OpenAI (o httpx). No usar LangChain.
6. **Base de Datos:** Crear migración en Alembic para `CREATE EXTENSION IF NOT EXISTS vector;` y agregar columna `embedding` (ej. `Vector(1536)`) en `tickets`.
