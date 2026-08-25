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
5.  **CORS Configurado:** Validación estricta con expresiones regulares que limita los orígenes de producción únicamente a subdominios del dominio principal (`*.tecnidesk.lat` y `*.adriansaas.xyz`) y orígenes de desarrollo especificados en variables de entorno.
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
*   **Despliegue de Inventario, Validaciones Estrictas y Resolución de CORS/500 (14 de Julio, 2026):** Se implementó el módulo completo de Inventario (frontend y backend). Se bloqueó la creación de piezas genéricas como "Display", forzando especificación de marca/modelo, y se impusieron validaciones numéricas estrictas (`Number.isFinite`, `Number.isInteger`). Se depuró un problema de despliegue donde Render y Vercel experimentaban rechazos cruzados; se ajustó la Regex del CORS (`(.*\.+)?(tecnidesk\.lat|adriansaas\.xyz)`) y se solucionó una severa inyección de dependencias defectuosa en `routers/inventory.py` que provocaba un 500 Internal Server Error (IntegrityError de Foreing Key en PostgreSQL) al inyectar `current_shop: Shop` sobre una función middleware (`subscription_guard`) que en realidad devuelve un `User`.
*   **Implementación del Módulo de Técnicos Completado (16 de Julio, 2026):** Se integró una arquitectura multi-tenant para la gestión de técnicos del taller. Incluye un CRUD completo, especialidades inferidas dinámicamente leyendo los diagnósticos/repuestos en el backend, un calculador de proxy de rendimiento (ingresos atribuidos), selectores de reasignación en UI (`AdminTicketCard` y `NewTicketModal`), y balanceo automático de carga (asignación al técnico menos saturado). Además, las pruebas de integración certificaron exitosamente la seguridad y el estricto aislamiento entre talleres.
*   **Optimización de Rendimiento Frontend (17 de Julio, 2026):** Se ejecutó un plan de 5 fases basado en diagnósticos de `react-doctor`. Se implementó *code splitting* (`React.lazy`/`Suspense`) reduciendo el tamaño del bundle inicial. Se eliminaron cuellos de botella de renderizado (`transition: "all"`) en componentes modales, sustituyéndolos por propiedades delegables a GPU (`opacity`, `transform`, `background-color`). Se integró `@tanstack/react-query` y `useTransition` para búsquedas y cargas concurrentes, erradicando los bloqueos del hilo principal.
*   **Resolución Falso Error CORS y Fuga de Caché Multi-Tenant (17 de Julio, 2026):** 
    *   *Crash MissingGreenlet:* Se añadió eager loading (`selectinload(Ticket.technician)`) en `ticket_service.py` resolviendo caídas asíncronas de Pydantic al serializar tickets asignados.
    *   *Falso CORS (Error 500 oculto):* Se inyectó un `global_exception_handler` en `main.py` para capturar excepciones fatales, asignar un `request_id` y envolverlas en un `JSONResponse` puro, permitiendo que el middleware de CORS estampe los headers correctamente.
    *   *Aislamiento en React Query:* Se reemplazó el vaciado estático de sessionStorage por un evento global (`auth:logout`) que ejecuta `queryClient.clear()` en `App.jsx`, purgando físicamente los datos privados del taller de la memoria RAM. Adicionalmente se desacopló `Promise.all` de las estadísticas y se parametrizó la política de reintentos (abortando de inmediato los 401/403).
*   **Fix Cierre de Sesión / React Error 321 (18 de Julio, 2026):** Se corrigió un error fatal de React en `App.jsx` que impedía el cierre de sesión (`auth:logout`). Se eliminó un llamado asíncrono anti-patrón (`import("react").then(...)`) que envolvía al hook `useEffect`, trasladando el hook al *top-level* del componente para respetar las Reglas de los Hooks.

*   **Testing, Paginación Server-Side y Fix de Búsqueda (24 de Julio, 2026):** Se instauró infraestructura fundacional de testing con `pytest` y `vitest`. Además, se implementó paginación offset (`limit`/`skip`) desde el servidor para los endpoints de Tickets e Inventario junto a una nueva entidad y router independiente para Clientes (`GET /clients`). La UI fue refactorizada para enviar peticiones de página y consumir respuestas unificadas del tipo `{ items, total }`. Finalmente, se corrigió un bug grave en la barra de búsqueda combinando un único parámetro de query `search` procesado en backend con operadores lógicos `OR` de SQLAlchemy para evaluar coincidentemente nombre de cliente, dispositivo e ID.
*   **Rediseño Visual Hallmark (Workbench + Atmospheric) (24 de Julio, 2026):** Se ejecutó una auditoría y rediseño de UI con la skill **Hallmark**, erradicando el patrón genérico de dashboard SaaS. Se actualizaron los estilos globales (`App.css`) a una paleta de color **OKLCH** limpia de sombras/gradientes sucios y se refactorizó `AdminDashboard.jsx` adoptando la macroestructura *Workbench* (Mesa de Trabajo) y la navegación flotante *N5 Floating Pill*. La lógica de estado, React Query y API permanecieron 100% intactas.
*   **Nombre de Taller Dinámico (Preparación Backend) (24 de Julio, 2026):** Se modificó `TokenResponse` y el servicio de login para interceptar el `business_name` de la tienda y devolverlo en el payload de inicio de sesión. `LoginPage.jsx` ahora lo almacena en `sessionStorage`. El frontend temporalmente mantiene un hardcode ("TecniDesk Admin") por motivos de captura de pantalla, pero la arquitectura está lista para inyectar dinámicamente `sessionStorage.getItem("td_shop")` en la barra de navegación en una iteración futura.
*   **Ocultamiento de Controladores (Preparación UI) (24 de Julio, 2026):** Se removió temporalmente del DOM el componente `<select>` de "Límite por página" en `AdminDashboard.jsx` para evitar que aparezca en el material gráfico promocional/capturas del proyecto. La lógica de estado de React (`limit`, `setLimit`) y el backend (`skip/limit`) siguen funcionando de forma predeterminada (10 por página) y quedan a la espera de ser expuestos nuevamente cuando se finalice la fase de captura.
*   **Afinación de Diseño y Fix de Inventario (24 de Julio, 2026):** Se corrigió un bug grave en `DiagnosticModal.jsx` (`p.some is not a function`) que ocurría porque el modal esperaba un array plano de repuestos, pero el endpoint `/inventory` había sido actualizado para retornar un objeto paginado `{ items, total }`. Se refinó también la "Floating Pill" (ancho máximo a 1050px, mayor espacio vertical con el área de trabajo, y flexbox para íconos de botones). Adicionalmente, se activó `color-scheme: dark` en el CSS base para garantizar que el ícono nativo del calendario (`type="date"`) se pinte de blanco en el tema atmosférico oscuro.
*   **Optimización Zero-Delay en Detalles de Ticket (24 de Julio, 2026):** Se refactorizó la carga de detalles en `AdminTicketCard.jsx`. Se eliminó un anti-patrón de fetch manual en un `useEffect` que provocaba parpadeos de carga de 2-3 segundos en cada apertura, migrándolo hacia `useQuery` con `initialData` del caché de React Query. Esto permite apertura de modal instantánea (Zero-Delay UI) y actualizaciones en segundo plano (stale-while-revalidate), ahorrando costos de servidor y sin requerir Redis.
*   **Modo Claro (Light Mode) con Paleta Ámbar / OKLCH (27 de Julio, 2026):** Se implementó una arquitectura de temas flexible con `ThemeContext` (React Context API) y `localStorage` (`tecnidesk-theme`). El componente `ThemeToggle.jsx` permite alternar dinámicamente entre el modo oscuro por defecto y el nuevo modo claro basado en variables CSS OKLCH alineadas con la paleta cálida ámbar (`[data-theme="light"]` en `App.css`). Integrado en `AdminDashboard`, `TrackingPortal` y `LoginPage`, con ciclo SDD completado y archivado.
*   **Privacidad y Enmascaramiento de PII + Botón Interactivo en Modal (27 de Julio, 2026):** Se creó el módulo de utilidades `src/utils/privacy.js` (`maskPhone`, `maskEmail`, `maskTrackingCode`) para proteger los datos sensibles de los clientes en la pantalla principal del mostrador y prevenir *shoulder surfing*. En las tarjetas iniciales del dashboard se enmascaran el teléfono (`09xxxxxxxx`), el correo (`clxxxxxxo@gmail.com`) y el código de guía (`#e0xxxxxx...`), y la fecha de ingreso omite la hora (`formatOnlyDate` en `src/utils/date.js`). En el modal de detalles (`AdminTicketCard.jsx`), los datos se abren ocultos por defecto y se incluye un botón con ícono de ojo (👁️ `Eye`/`EyeOff`) con estado local (`showPii`) para que el técnico pueda revelar los datos completos al hacer clic. Ciclo SDD completado y archivado.
*   **Ajuste de Paginación y Resaltado Tipográfico (27 de Julio, 2026):** Se aumentó el límite inicial de tarjetas de 10 a 15 por página (`setLimit(15)`) en `AdminDashboard.jsx`. Además, se reforzó el contraste y peso de la tipografía en las tarjetas estadísticas (`.admin-stat-label`) fijándola en extra negrita (`font-weight: 800`), 12px y mayor legibilidad en modo claro.
*   **Diagnóstico Asistido con Razonamiento Explicable y RAG Híbrido (20-22 de Agosto, 2026 - Completado):**
    *   *Fases 1 y 2 (Infraestructura, Embeddings y Retrieval Híbrido):* Habilitada extensión `vector` (pgvector), tablas de diagnóstico (`diagnostic_cases`, etc.) con índices HNSW (768 dims). Servicio de embeddings (`EmbeddingService`) con Ollama (`nomic-embed-text-v2-moe`) y fallback resiliente. Base de conocimiento sintética y retrieval multi-tenant aislado por `shop_id`.
    *   *Fase 3 (Razonamiento Explicable con Gemini 3.7 Flash):* Generación de explicaciones y citaciones grounded con validación determinística anti-alucinación.
    *   *Fase 4 (Human-in-the-Loop):* Chat interactivo de corrección para técnicos y aprendizaje incremental (guardado automático de casos `real_validated`).
    *   *Fase 5 (Frontend & Métricas):* Componente `DiagnosticAssistPanel.jsx` integrado en el modal de diagnóstico y endpoint de madurez del RAG. Suite respaldada con 48 tests (`pytest`, `respx`). SDD archivado en `openspec/changes/archive/`.
*   **Restauración de Controles UI y Fix de Tarjetas Workbench (22 de Agosto, 2026):**
    *   *Nombre de Taller Dinámico:* Inyección de `sessionStorage.getItem("td_shop")` en el Navbar del panel administrativo con fallback seguro a "TecniDesk Admin".
    *   *Control de Paginación:* Reincorporación del selector `<select>` en `AdminDashboard.jsx` para alternar límites por página (10, 15, 20, 50) enlazado al estado de React y reset de página.
    *   *Corrección de Padding en Tarjeta:* Añadido `padding: "0 20px"` al contenedor `.ticket-card-signals` en `AdminTicketCard.jsx` para evitar que los iconos y badges de excepciones toquen o pisen el borde de la tarjeta. SDD archivado en `openspec/changes/archive/2026-08-22-restore-ui-controls/`.
*   **Workbench Operativo Mínimo (Fase 1 y 1.1 completadas) (21 de Agosto, 2026):**
    *   *Optimización y N+1:* Se eliminó la petición a `/evidences` al montar tarjetas, cargando la galería on-demand al abrir el modal.
    *   *Señales Operativas (UI):* Rediseño del `AdminTicketCard` ocultando información pasiva y destacando urgencias (badges `Sin técnico`, `Vencido`, `Listo p/ retiro`).
    *   *Smart Action CTA:* Un botón contextual de prioridad estricta (*Asignar* -> *Diagnosticar* -> *WhatsApp* -> *Ver detalle*) para guiar al técnico en la próxima acción necesaria.
    *   *Filtros y KPIs:* Los 4 indicadores del Dashboard ahora funcionan como filtros asíncronos combinados con paginación optimizada.
    *   *Ordenamiento Inteligente (Backend):* Refactor de `list_tickets` integrando un `CASE` (SQL) que fuerza al tope de la lista los equipos sin técnico (`technician_id IS NULL`), luego los vencidos (`>72h`), y finalmente por orden cronológico. 100% test coverage y baseline métrico extraído (evidenciando un backlog crítico pre-lanzamiento del 79% sin técnico).

*   **Workbench Operativo (Fase 2 Completada) (22 de Agosto, 2026):**
    *   *Tabla de Auditoría (`ticket_status_history`):* Modelo ORM SQLAlchemy 2.0 y migración Alembic (`b2c3d4e5f6a7`) para registrar de forma síncrona e inmutable cada transición de estado con autor, timestamp y motivo.
    *   *Bloqueo Estricto de Técnico:* Validación de guardias en `ticket_service.py` que lanza `UnassignedTechnicianError` (HTTP 400 Bad Request) si se intenta avanzar a `EN_REPARACION` sin un técnico responsable asignado.
    *   *SLA Dinámico por Estado:* Motor de SLA relativo a `updated_at` con umbrales específicos (`EN_REVISION`: 24h, `EN_ESPERA_INGRESO`: 48h, `EN_REPARACION`: 48h) y estados pausados (`ESPERANDO_APROBACION`, `ESPERANDO_REPUESTO`, `LISTO_PARA_RETIRAR`). Refactor del ordenamiento SQL del Workbench (`technician_id IS NULL` > SLA vencido > `created_at DESC`).
    *   *Suite Combinatoria de Tests:* 17 nuevos tests unitarios en `test_ticket_guards.py` e integración en `test_tickets.py` alcanzando 67/67 tests pasando en verde (100%). Ciclo SDD archivado en `openspec/changes/archive/2026-08-22-workbench-operativo-fase2/`.

*   **Workbench Operativo (Fase 3 Completada: Vista Kanban) (22 de Agosto, 2026):**
    *   *Tablero Visual Kanban:* Componentes modulares (`KanbanBoard.jsx`, `KanbanColumn.jsx`, `KanbanTicketCard.jsx`) organizando el flujo del taller en 5 columnas operativas (*Ingreso/Recepción*, *En Revisión & Diagnóstico*, *Presupuesto & Espera*, *En Reparación*, *Listo para Retirar*).
    *   *Alternador de Vista con Persistencia:* Selector de vistas (Lista vs. Kanban) en la barra de herramientas del `AdminDashboard.jsx`, con memoria persistente en `localStorage` (`tecnidesk_workbench_view`).
    *   *Avance Rápido y Respeto a Guardias de Fase 2:* Botón de transición ágil entre estados que intercepta avances a `EN_REPARACION` para exigir asignación de técnico antes de mutar el estado.
    *   *Tarjetas de Alta Densidad y SLA Visual:* Vista compacta con badges de técnico, alertas de SLA dinámico vencido en rojo y apertura instantánea del modal de detalles unificado (`TicketDetailModal.jsx`).
*   **Workbench Operativo (Fase 4 Completada: SLAs Multi-tenant Configurables) (22 de Agosto, 2026):**
    *   *Persistencia Multi-Tenant:* Columna `sla_config` (JSON) en la tabla `shops` mediante migración Alembic (`b3c4d5e6f7a8`), con fallback robusto a valores por defecto del sistema (`DEFAULT_SLA_THRESHOLDS_HOURS`).
    *   *API REST y Seguridad:* Endpoints `GET /shops/sla-config` y `PATCH /shops/sla-config` protegidos por `admin_guard`, con validación estricta de rangos de 1 a 720 horas y filtrado automático de claves no válidas.
    *   *Ordenamiento SQL Dinámico por Taller:* Las consultas de tickets en `ticket_service.py` calculan la prioridad de ordenamiento (`is_ticket_sla_breached`) usando los umbrales personalizados de la tienda en sesión.
    *   *Panel de Ajustes en UI:* Componente modal [`SlaSettingsModal.jsx`](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/SlaSettingsModal.jsx) con botón "Configurar SLAs" en la barra de herramientas del `AdminDashboard.jsx`, permitiendo ajuste en tiempo real, validación visual y botón "Restablecer Defaults".
    *   *Verificación y Calidad:* 115 tests de backend en Pytest (100% pasando) y 62 tests de frontend en Vitest (100% pasando). Ciclo SDD archivado en `openspec/changes/archive/2026-08-22-workbench-operativo-fase4-sla-config/`.

*   **Workbench Operativo (Fase 5 Completada: Analítica de Tiempos de Ciclo y Cuellos de Botella) (22 de Agosto, 2026):**
    *   *Motor de Analítica Operativa:* Función `get_workshop_cycle_time_metrics` en `ticket_service.py` que calcula sobre `ticket_status_history` el Lead Time promedio (ingreso a entrega), el Cycle Time activo (`EN_REPARACION`), el desglose de horas promedio por cada etapa, el cuello de botella principal del taller y el porcentaje de cumplimiento de SLA contra los umbrales de la tienda.
    *   *Endpoint REST Seguro:* `GET /tickets/analytics/cycle-times` registrado en `routers/tickets.py` antes de las rutas dinámicas para prevenir colisiones, resguardado por `admin_guard`.
    *   *Modal de Métricas en UI:* Componente [`CycleTimeAnalyticsModal.jsx`](file:///Users/adrianjosesoriano/Documents/Tecnidesk/frontend/src/features/admin/components/CycleTimeAnalyticsModal.jsx) accesible mediante el botón "Métricas y Tiempos" (`<BarChart3 size={16} />`) en `AdminDashboard.jsx`, con tarjetas KPI, selector de periodos (7, 30, 90 días), barras de progreso nativas en CSS y alerta visual sobre la etapa cuello de botella.
    *   *Verificación y Calidad:* 121 tests de backend en Pytest (100% pasando) y 74 tests de frontend en Vitest (100% pasando). Ciclo SDD archivado en `openspec/changes/archive/2026-08-22-workbench-operativo-fase5-cycle-times/`.

*   **Portal de Técnico & Copiloto IA Conversacional (23 de Agosto, 2026 - Completado):**
    *   *Backend & Seguridad:* Doble blindaje en rate limiting con SlowAPI key por `user_id` (`get_user_rate_limit_key`), rate limit en `POST /tickets/{id}/reveal-pin` (15/min), guard de ownership de tickets `verify_ticket_technician_access` (HTTP 403 en tickets ajenos), endpoint seguro `GET /technicians/me` con schema whitelist `TechnicianMeResponse`, auto-asignación `POST /tickets/{id}/assign-me`, revelado de PIN seguro con auditoría `POST /tickets/{id}/reveal-pin`, endpoint de chat libre `POST /diagnostic/chat`, y script de sincronización `backend/scripts/sync_technicians_users.py`.
    *   *Frontend & UX del Técnico:* Enrutamiento inteligente en `/login` (`td_role` a `/tech` o `/admin`), matriz de roles en `ProtectedRoute`, Dashboard del Técnico (`/tech`) con pestañas "Mis Asignaciones" y "Equipos Disponibles", modo supervisor de solo lectura para `admin` en `/tech` (sin mutaciones ni chat visible), tarjetas de alta densidad, modal de trabajo rápido (`TechnicianWorkModal.jsx`) con toggle `Eye`/`EyeOff` de PIN revelado, y Copiloto IA con burbuja flotante FAB (`AiChatBubble.jsx`) y panel lateral deslizable (`AiChatDrawer.jsx`) con integración bidireccional a la orden y confirmación de aprendizaje RAG (`pgvector`).
    *   *Verificación y Calidad:* 130 tests de backend en Pytest (100% pasando) y 97 tests de frontend en Vitest (100% pasando), build de producción exitoso.

*   **Generación de Acceso a Técnicos, Async IO, Estabilización Gemini y Renombramiento a Ohm (25 de Agosto, 2026):**
    *   *Generar Acceso a Técnicos:* Endpoint `POST /technicians/{id}/access` con generación de contraseñas temporales y despacho seguro vía Resend con manejo de errores 409 y 502. Integración en `TechniciansModal.jsx` con soporte para técnicos fantasma.
    *   *Fix technician_id en Chat:* Corrección en `routers/tickets.py` para mapear el ID real del técnico (`Technician.user_id == current_user.id`) en lugar de `current_user.id` al registrar conversaciones de diagnóstico.
    *   *Refactor Async I/O & Salvaguarda:* Migración de llamadas de Gemini a la API asíncrona (`client.aio.models.generate_content`) y Resend a `run_in_threadpool`. Salvaguarda de latencia de event loop (<50ms) en `test_async_blocking.py`.
    *   *Estabilización de IA & Benchmark:* Diagnóstico y resolución de errores 503 por saturación global en `gemini-3.7-flash`, migrando formalmente a **`gemini-3.6-flash`** en toda la plataforma tras pruebas de latencia (~6.8s por respuesta con calidad técnica).
    *   *Identidad del Asistente ("Ohm"):* Renombramiento integral del copiloto a **Ohm** (unidad eléctrica) en backend y componentes de UI (`AiChatBubble.jsx`, `AiChatDrawer.jsx`, `TechnicianDashboard.jsx`, `TechnicianWorkModal.jsx`).
    *   *Verificación y Testing:* 142 tests en backend (Pytest) y 97 tests en frontend (Vitest) pasando al 100%.

### 6.2 Estado del Workbench y Portal de Técnico
*   **Módulo Workbench y Portal de Técnico Completo:** 100% implementado, respaldado por testing automatizado, blindaje multi-tenant, enrutamiento por roles y archivado formalmente bajo la metodología Spec-Driven Development (SDD).

