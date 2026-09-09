# Specification: Ohm Administrative Assistant

## Capability: admin-assistant-query
Provides conversational shop-level metrics and operational insights for workshop administrators through a closed-intent, deterministic query pipeline.

### Requirement: Admin Access Control
The system MUST protect the admin assistant query endpoint with `admin_guard`.

#### Scenario: Authorized admin queries assistant
- **Given** an authenticated user with role `admin`
- **And** an active shop subscription
- **When** `POST /admin/assistant/query` is invoked with a valid message payload
- **Then** the request is accepted with HTTP 200 OK.

#### Scenario: Technician is rejected
- **Given** an authenticated user with role `technician`
- **When** `POST /admin/assistant/query` is invoked
- **Then** the request is rejected with HTTP 403 Forbidden.

### Requirement: Intent Classification and Execution
The system MUST classify incoming messages against the closed intent catalog v1 and execute deterministic queries without exposing arbitrary SQL execution.

#### Scenario: Querying today's revenue (ganancias_del_dia)
- **Given** an authenticated admin
- **When** the message matches queries regarding daily revenue or earnings (e.g. "cuánto hemos ganado hoy" or "ganancias del día")
- **Then** the system executes the deterministic revenue aggregation for the current shop and day
- **And** returns a natural language summary containing the calculated amount in USD.

#### Scenario: Querying today's intake volume (equipos_ingresados_hoy)
- **Given** an authenticated admin
- **When** the message matches queries regarding tickets created today (e.g. "cuántos equipos entraron hoy" or "ingresos de hoy")
- **Then** the system executes the deterministic count of tickets created today for the shop
- **And** returns a natural language summary containing the exact count.

#### Scenario: Querying stale/untouched devices (equipos_sin_tocar)
- **Given** an authenticated admin
- **When** the message matches queries regarding stale tickets or untouched equipment (e.g. "equipos sin tocar" or "tickets varados")
- **Then** the system executes the deterministic count and listing of active tickets without updates for >48 hours
- **And** returns a natural language summary specifying the count of affected devices.

#### Scenario: Unrecognized query fallback
- **Given** an authenticated admin
- **When** the message does not match any recognized intent in the closed catalog
- **Then** the system does not execute any database mutations or open-ended SQL queries
- **And** returns a canned response listing the supported query intents.

### Requirement: Tenant Data Isolation
The system MUST scope all query aggregations strictly to the administrator's `shop_id`.

#### Scenario: Strict shop boundary
- **Given** Admin A belonging to Shop A and Admin B belonging to Shop B
- **When** Admin A queries daily metrics
- **Then** only data with `shop_id == Shop A.id` is included in the aggregation, with zero data leakage from Shop B.

### Requirement: Frontend Admin Presentation
The frontend MUST configure `AiChatDrawer` for administrative mode when mounted in the admin dashboard.

#### Scenario: Quick chips rendering in admin mode
- **Given** an admin user opening Ohm in the admin dashboard (`context="admin"`)
- **Then** the drawer renders 3 quick chips: "Ganancias de hoy", "Equipos ingresados", and "Equipos sin tocar"
- **And** hides technician ticket diagnostic actions (such as apply to diagnosis or RAG confirmation).
