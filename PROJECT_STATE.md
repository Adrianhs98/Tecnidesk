# TecniDesk — Auditoría y Estado del Proyecto (PROJECT_STATE.md)

Este documento detalla los resultados de la auditoría técnica realizada sobre el sistema **TecniDesk**, un Micro SaaS Multi-Tenant diseñado para la gestión de talleres de reparación de celulares (adaptado para el mercado ecuatoriano).

---

## 1. Resumen Ejecutivo
**TecniDesk** es una solución web moderna con arquitectura desacoplada:
*   **Backend:** API REST robusta construida con **FastAPI**, persistencia asíncrona mediante **SQLAlchemy 2.0** + **asyncpg** sobre **PostgreSQL**, y migraciones controladas con **Alembic**.
*   **Frontend:** Aplicación de página única (SPA) de alta fidelidad visual y rendimiento impecable usando **React 19**, **Vite 7**, **Tailwind CSS v4** y **TypeScript**.

El sistema cuenta con un flujo seguro de control de inquilinos (multi-tenancy) basado en subdominios únicos, seguridad robusta para el almacenamiento de datos del cliente (encriptación simétrica Fernet de contraseñas de dispositivos), y un portal público integrado para que el usuario final pueda consultar y autorizar presupuestos en tiempo real.

---

## 2. Estructura General del Espacio de Trabajo
El espacio de trabajo está dividido en dos grandes directorios independientes en la raíz del proyecto:
*   `Tecnidesk-backend/` - API REST en Python.
*   `Tecnidesk-frontend/` - Cliente React con Vite.

---

## 3. Auditoría del Backend (`Tecnidesk-backend`)

### 3.1 Estructura de Directorios
```
Tecnidesk-backend/
├── app/
│   ├── api/v1/                # Endpoint y enrutado para la API pública (tracking de tickets)
│   ├── core/                  # Dependencias de seguridad, JWT, rate-limit y guards
│   ├── models/                # Modelos ORM de SQLAlchemy 2.0
│   ├── routers/               # Controladores de la API (Auth, Shops, Tickets, Health)
│   ├── schemas/               # Validaciones y serialización de datos con Pydantic v2
│   ├── services/              # Lógica de negocio (Auth, Email, Storage, Tickets, Shops)
│   ├── config.py              # Configuración de entornos usando Pydantic Settings
│   ├── database.py            # Motor de conexión a base de datos asíncrono
│   └── main.py                # Punto de entrada principal (FastAPI, CORS, middlewares)
├── alembic/                   # Entorno de control de migraciones de base de datos
├── scripts/                   # Scripts auxiliares (Seed de la BD, activación manual de tiendas)
├── requirements.txt           # Dependencias del backend (FastAPI, asyncpg, cryptography, etc.)
└── alembic.ini                # Configuración de Alembic
```

### 3.2 Base de Datos y Modelos ORM
La base de datos utiliza PostgreSQL con la extensión `uuid-ossp` para generación de IDs de tipo UUIDv4 de forma nativa. 

Los modelos ORM están definidos en `app/models/` y heredan de una clase base común en `app/models/base.py` que provee mixins para UUIDs y marcas de tiempo (`created_at`, `updated_at`).

*   **Plan (`plans`):** Define los planes de suscripción disponibles para los talleres (ej: plan "Todo Incluido" a $17.00 USD/mes).
*   **Shop (`shops`):** Almacena las tiendas (inquilinos/tenants) asociadas a un subdominio único (`subdomain`), estado de suscripción denormalizado (`subscription_status`), datos de contacto y sesión de WhatsApp.
*   **Subscription (`subscriptions`):** La fuente de verdad del estado de pago y validez de la suscripción del taller.
*   **User (`users`):** Personal del taller, clasificado por rol (`admin` o `technician`). Almacena los hashes de contraseñas con bcrypt y tokens de restablecimiento de contraseña.
*   **RefreshToken (`refresh_tokens`):** Tabla estatal para almacenar los hashes SHA-256 de los refresh tokens emitidos para una rotación de un solo uso.
*   **Customer (`customers`):** Clientes del taller de reparación. Cuenta con un **índice compuesto** (`shop_id`, `phone_number`) para búsquedas ultra rápidas de clientes.
*   **Inventory (`inventory`):** Catálogo de repuestos y mano de obra con alertas de stock bajo (`low_stock_alert`).
*   **Ticket (`tickets`):** Orden de reparación principal con información del dispositivo (marca, modelo, diagnóstico, notas internas, costo total y un `tracking_token` auto-generado para accesos públicos).
*   **TicketItem (`ticket_items`):** Repuestos específicos e insumos/mano de obra asociados a un ticket.
*   **TicketEvidence (`ticket_evidences`):** Registro de fotos y archivos subidos a almacenamiento en la nube (Cloudflare R2) para evidenciar el estado del dispositivo.
*   **WebhookLog (`webhook_logs`):** Historial de llamadas a webhooks externos desencadenadas por cambios en los estados de los tickets.

### 3.3 Mecanismos de Seguridad Implementados
1.  **Aislamiento Multi-Tenant:** Todos los endpoints de gestión requieren autenticación y comprueban estrictamente que las entidades pertenezcan al `shop_id` asociado al usuario en sesión.
2.  **Suscripción Guard (`subscription_guard`):** Middleware de nivel de ruta que comprueba la vigencia de la suscripción de la tienda consultando directamente la tabla `subscriptions` (fuente de verdad). Si la suscripción ha expirado, está suspendida o cancelada, deniega el acceso con un error HTTP 402 (Payment Required).
3.  **Encriptación Simétrica de PIN/Contraseña:** La contraseña o PIN de desbloqueo del celular ingresado (`pin_or_password`) se cifra utilizando **Fernet** (`cryptography`) antes de persistirse en la base de datos y solo se desencripta en la capa de servicios interna, evitando filtrarse en los esquemas públicos de la API.
4.  **Autenticación Robusta:** Acceso basado en JWT asimétricos con tokens de corta duración (60 minutos) y refresh tokens estatales de larga duración (7 días) que implementan rotación de un solo uso (Single-Use Rotation) para prevenir ataques de replay.
5.  **CORS Configurado:** Validación estricta con expresiones regulares que limita los orígenes de producción únicamente a subdominios del dominio principal (`*.adriansaas.xyz`) y orígenes de desarrollo especificados en variables de entorno.
6.  **Rate Limiting:** Se utiliza la librería `slowapi` para proteger rutas vulnerables como `/auth/login` (máximo 5 intentos/min por dirección IP) y `/public/ticket/{token}` (30 consultas/min por IP).

---

## 4. Auditoría del Frontend (`Tecnidesk-frontend`)

### 4.1 Estructura de Directorios
```
Tecnidesk-frontend/
├── src/
│   ├── api/                   # Configuración del endpoint base y helper fetch con auth (`authFetch.js`)
│   ├── components/            # Componentes globales de la app
│   │   ├── guards/            # Protectores de rutas (`ProtectedRoute`, `PublicRoute`)
│   │   └── shared/            # Componentes visuales comunes (Logo, Skeleton, Stepper, etc.)
│   ├── features/              # Módulos específicos de la aplicación
│   │   └── admin/             # Panel administrativo de la tienda
│   │       ├── components/    # Tarjetas de tickets y modales para ingresar equipos/ver detalles
│   │       └── AdminDashboard.jsx
│   ├── pages/                 # Páginas principales de la aplicación (Home, Login, Register, Portal)
│   ├── utils/                 # Constantes de estados, formateo de fechas y utilidades
│   ├── App.css                # Estilos generales y variables del tema
│   ├── App.jsx                # Definición de rutas y enrutador React Router
│   ├── index.css              # Archivo de entrada de estilos Tailwind CSS
│   └── main.tsx               # Renderizado e inicialización de la app React
├── public/                    # Archivos estáticos públicos
├── package.json               # Dependencias de npm y scripts
└── vite.config.ts             # Configuración de empaquetado Vite
```

### 4.2 Arquitectura del Cliente
1.  **Tecnologías de Vanguardia:** Se utiliza la última versión de **React 19** que incorpora mejoras de rendimiento en el ciclo de renderizado, empaquetado rápido mediante **Vite 7**, y **Tailwind CSS v4** integrado nativamente para un diseño fluido y moderno.
2.  **Enrutado Seguro:** Se emplea `react-router-dom` (v7) con componentes de orden superior para proteger el panel de administración (`ProtectedRoute` redirige a `/login` si no se detecta JWT activo) y restringir el acceso a formularios de login/onboarding a usuarios ya autenticados (`PublicRoute` redirige a `/admin`).
3.  **Compresión de Imágenes del Lado del Cliente:** Al subir evidencias (fotos del estado del celular roto), el frontend utiliza `browser-image-compression` para comprimir la imagen localmente por debajo de 800 KB antes del envío HTTP, ahorrando ancho de banda y garantizando que se cumpla el límite estricto de 2 MB del backend.
4.  **Flujos de Consulta en Tiempo Real:** El portal de tracking público (`/tracking/:token`) consume la API sin requerir credenciales, mostrando una línea de tiempo dinámica interactiva (Stepper) y banners informativos cuando el dispositivo requiere la intervención o autorización del cliente para iniciar la reparación.

---

## 5. Auditoría de Seguridad y Cumplimiento
| Aspecto de Seguridad | Estado | Componente / Archivo | Notas de Auditoría |
| :--- | :---: | :--- | :--- |
| **Aislamiento Multi-tenant** | ✅ Correcto | `app/core/dependencies.py` | Validado en cada solicitud a través de la relación de usuarios e inquilinos. |
| **Protección de Datos Sensibles** | ✅ Correcto | `app/models/ticket.py` | La contraseña del dispositivo se almacena encriptada simétricamente (Fernet). |
| **Protección contra Fuerza Bruta** | ✅ Correcto | `app/routers/auth.py` | Rate limiter slowapi activo a 5 req/min en login por IP. |
| **Control de Caducidad de Planes** | ✅ Correcto | `app/core/dependencies.py` | Bloqueo automático HTTP 402 en la base del guard. |
| **Gestión de Sesión / R2** | ✅ Correcto | `app/routers/tickets.py` | Limitador de tamaño de archivo (2MB) y validación de tipos MIME reales. |
| **Restablecimiento de Password** | ✅ Correcto | `app/services/auth_service.py` | Uso de tokens únicos expirable con integración Resend. |

---

## 6. Estado Actual de la Base de Código
El proyecto se encuentra en una etapa madura de MVP, con sus funcionalidades core completamente funcionales y optimizadas. 

### 6.1 Correcciones Recientes (Mergeadas)
*   **FASE 1 (BUG-02):** Se resolvió la pérdida de datos del cliente al cambiar estados en el panel, implementando `selectinload` en SQLAlchemy y preservando el estado local en React.
*   **FASE 2 (BUG-01):** Se corrigió la desaparición del PIN y correo al crear tickets forzando al endpoint POST a devolver un esquema anidado completo (`TicketListResponse`).
*   **FASE 3 (BUG-03):** Se habilitó la subida de evidencia fotográfica inicial directamente desde el modal de creación, implementando un pipeline secuencial con `FormData` nativo.
*   **FASE 5 (Estadísticas Reales — RESUELTA):** Se implementó el endpoint dedicado `GET /tickets/stats` en `app/routers/tickets.py` (declarado antes de `/{ticket_id}` para evitar colisión con UUIDs). La lógica `get_ticket_stats()` en `app/services/ticket_service.py` calcula los conteos en una sola consulta agregada con `COUNT() FILTER (WHERE ...)` nativo de PostgreSQL. El esquema de respuesta es `TicketStatsResponse` (`app/schemas/ticket.py`). El frontend `AdminDashboard.jsx` consume ambos endpoints en paralelo con `Promise.all` y aplica *optimistic updates* al crear/cambiar estado. **Ya no se usa `tickets.length` para los totales.**
*   **Reparación de PIN en actualizaciones (RESUELTO):** Las tres funciones administrativas `update_ticket_status`, `update_ticket_diagnostic` y `assign_technician` en `app/services/ticket_service.py` ahora desencriptan el PIN (`decrypt_pin`) y lo adjuntan como `device_password` antes de retornar, evitando que el frontend muestre "Sin PIN" tras una actualización. Plan original documentado en `PLAN_REPARACION_PIN.md`.
*   **Refactorización del Botón de WhatsApp en Tracking Público:** Se solucionó el bug de renderizado originado por strings vacíos en la base de datos corrigiendo el esquema de registro (`RegisterRequest` en backend) para que Pydantic acepte e inserte `contact_whatsapp`. Adicionalmente, se consolidaron los botones de WhatsApp redundantes del frontend (`TrackingPortal.jsx`) en una única llamada a la acción contextualizada en la etapa de presupuestación, incorporando un microcopy optimizado para facilitar la negociación de presupuestos en dólares.
*   **Análisis de Repuestos y Vistas de Supabase (8 de Julio, 2026 - Tesis):** Se analizó la estructura de `ticket_items` y su relación opcional con `inventory` (`inventory_id` nullable). Se estructuraron 5 vistas SQL persistentes (`v_reparaciones_completas`, `v_ranking_piezas`, `v_piezas_por_marca_modelo`, `v_alerta_compra_urgente`, `v_rentabilidad_piezas`) y un catálogo de 8 queries analíticas en el editor de Supabase. Esto permite automatizar reportes para la tesis y analizar marcas, modelos, rentabilidad y demanda de repuestos para importaciones.
*   **Implementación de Analíticas y Fix UI (10 de Julio, 2026):** Se crearon las 5 vistas en Supabase y se corrigió el script de inyección de datos agregando `gen_random_uuid()` dado que la migración carecía de `server_default`. Además, se arregló el CSS del selector de estados en `AdminTicketCard` usando `flex: 1 1 auto` y `min-width` para evitar recortes, y se ajustó el footer con `flex-wrap`.
*   **Fix CI/CD (Vercel y Render) (10 de Julio, 2026):** Se reconstruyeron los repositorios Git independientes para `frontend` y `backend`. Se corrigió un error en `.gitignore` del backend excluyendo `!requirements.txt` para que Render pudiera construir el proyecto, y se conectó correctamente el frontend en Vercel con la variable de entorno `VITE_API_URL` forzando un redeploy limpio desde la rama principal.
*   **Integración Metabase e Inventario (10 de Julio, 2026 - Tarde):** Se habilitó la vista analítica de stock crítico (`v_alerta_compra_urgente`). Se ejecutó el script `setup_inventario_metabase.py` para analizar consumos previos en `ticket_items`, poblar dinámicamente `inventory` con stocks iniciales y establecer llaves foráneas (`inventory_id`). La vista SQL fue refactorizada con `LEFT JOIN` para calcular consumos dinámicos en tiempo real, completando el dashboard de la tesis.
*   **Refactor UI/UX de Diagnóstico y Optimización de Dashboard (13 de Julio, 2026):**
    *   *Bug de Pantalla Negra / React Crash:* Corregido al extraer `DiagnosticModal` de manera independiente para evitar el backdrop persistente y agregando `parseFloat()` para evitar crashes por parseo de `toFixed` sobre strings del backend en `total_cost`.
    *   *Mano de Obra:* Eliminado por completo el input de mano de obra del diagnóstico.
    *   *Selector Rápido:* Añadidas 4 opciones de reparación rápida predefinidas (Flex, Batería, Display, Custom) combinadas con carga dinámica de inventario.
    *   *Optimización de Filtros:* Unificados los campos de búsqueda, filtros de tiempo, calendario de fecha y botones de acción en una sola fila en PC (`.admin-filters-bar` en `App.css`) manteniendo comportamiento responsivo.
*   **Despliegue de Inventario, Validaciones Estrictas y Resolución de CORS/500 (14 de Julio, 2026):** Se implementó el módulo completo de Inventario (frontend y backend). Se bloqueó la creación de piezas genéricas como "Display", forzando especificación de marca/modelo, y se impusieron validaciones numéricas estrictas (`Number.isFinite`, `Number.isInteger`). Se depuró un problema de despliegue donde Render y Vercel experimentaban rechazos cruzados; se ajustó la Regex del CORS (`(.*\.+)?adriansaas\.xyz`) y se solucionó una severa inyección de dependencias defectuosa en `routers/inventory.py` que provocaba un 500 Internal Server Error (IntegrityError de Foreing Key en PostgreSQL) al inyectar `current_shop: Shop` sobre una función middleware (`subscription_guard`) que en realidad devuelve un `User`.
### 6.2 Deuda Técnica y Pendientes Críticos
*   **FASE 4 (Vulnerabilidad IDOR en Activación):** El endpoint `/admin/activate-shop` (en `app/routers/tickets.py`) actualmente solo verifica un usuario autenticado genérico mediante `get_current_user`. Debe restringirse exclusivamente a super-administradores del sistema SaaS (no existe aún ningún `admin_guard` ni rol super-admin en el backend).
