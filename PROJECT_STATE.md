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
*   `backend/` - API REST en Python (FastAPI, pgvector, SQLAlchemy async).
*   `frontend/` - Cliente React 19 con Vite 7 y Tailwind CSS v4.

---

## 3. Auditoría del Backend (`backend`)

### 3.1 Estructura de Directorios
```
backend/
├── app/
│   ├── api/v1/                # Endpoint y enrutado para la API pública (tracking de tickets)
│   ├── core/                  # Dependencias de seguridad, JWT, rate-limit y guards
│   ├── models/                # Modelos ORM de SQLAlchemy 2.0
│   ├── routers/               # Controladores (Auth, Shops, Tickets, Technicians, Clients, Inventory, Diagnostic, etc.)
│   ├── schemas/               # Validaciones y serialización de datos con Pydantic v2
│   ├── services/              # Lógica de negocio (Tickets, Diagnostic, LLM Gateway, Tavily, Safety, etc.)
│   ├── config.py              # Configuración de entornos usando Pydantic Settings
│   ├── database.py            # Motor de conexión a base de datos asíncrono
│   └── main.py                # Punto de entrada principal (FastAPI, CORS, middlewares)
├── alembic/                   # Entorno de control de migraciones de base de datos
├── scripts/                   # Scripts auxiliares (Seed de la BD, sincronización y mantenimiento)
├── tests/                     # 243 tests unitarios y de integración con pytest y respx
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
*   **TicketStatusHistory (`ticket_status_history`):** Registro inmutable de transiciones de estado de los tickets, con motivo, autor y marca de tiempo.
*   **Technician (`technicians`):** Perfiles técnicos del taller, especialidad declarada, datos de contacto y vinculación con la cuenta de usuario.
*   **DiagnosticCase (`diagnostic_cases`):** Base de conocimiento diagnóstica con embeddings vectoriales de 768 dimensiones (`pgvector` HNSW) para casos sintéticos y validados.
*   **DiagnosticConversation (`diagnostic_conversations`):** Hilos de chat conversacional del copiloto Ohm asociados a tickets o libres.
*   **DiagnosticMessage (`diagnostic_messages`):** Mensajes individuales del técnico y de Ohm dentro de la conversación.
*   **DiagnosticQueryLog (`diagnostic_query_logs`):** Métricas de madurez diagnóstica y auditoría de consultas al motor RAG.
*   **AiSecurityEvent (`ai_security_events`):** Registro inmutable de eventos de seguridad y detección de intentos de prompt injection en el copiloto Ohm.
*   **WebhookLog (`webhook_logs`):** Historial de llamadas a webhooks externos desencadenadas por cambios en los estados de los tickets.

### 3.3 Mecanismos de Seguridad Implementados
1.  **Aislamiento Multi-Tenant:** Todos los endpoints de gestión requieren autenticación y comprueban estrictamente que las entidades pertenezcan al `shop_id` asociado al usuario en sesión.
2.  **Suscripción Guard (`subscription_guard`):** Middleware de nivel de ruta que comprueba la vigencia de la suscripción de la tienda consultando directamente la tabla `subscriptions` (fuente de verdad). Si la suscripción ha expirado, está suspendida o cancelada, deniega el acceso con un error HTTP 402 (Payment Required).
3.  **Encriptación Simétrica de PIN/Contraseña:** La contraseña o PIN de desbloqueo del celular ingresado (`pin_or_password`) se cifra utilizando **Fernet** (`cryptography`) antes de persistirse en la base de datos y solo se desencripta en la capa de servicios interna, evitando filtrarse en los esquemas públicos de la API.
4.  **Autenticación Robusta:** Acceso basado en JWT asimétricos con tokens de corta duración (60 minutos) y refresh tokens estatales de larga duración (7 días) que implementan rotación de un solo uso (Single-Use Rotation) para prevenir ataques de replay.
5.  **CORS Configurado:** Validación estricta con expresiones regulares que limita los orígenes de producción únicamente a subdominios del dominio principal (`*.tecnidesk.lat` y `*.adriansaas.xyz`) y orígenes de desarrollo especificados en variables de entorno.
6.  **Rate Limiting:** Se utiliza la librería `slowapi` para proteger rutas vulnerables como `/auth/login` (máximo 5 intentos/min por dirección IP) y `/public/ticket/{token}` (30 consultas/min por IP).

---

## 4. Auditoría del Frontend (`frontend`)

### 4.1 Estructura de Directorios
```
frontend/
├── src/
│   ├── api/                   # Clientes HTTP con authFetch y endpoints tipados
│   ├── components/            # Componentes globales de la app
│   │   ├── guards/            # Protectores de rutas (`ProtectedRoute`, `PublicRoute`)
│   │   └── shared/            # Componentes visuales comunes (Logo, Skeleton, Stepper, StatusBadge, etc.)
│   ├── context/               # ThemeContext (Modo Claro/Oscuro OKLCH)
│   ├── features/              # Módulos específicos de la aplicación
│   │   ├── admin/             # Panel administrativo Workbench y asistente Ohm
│   │   ├── analytics/         # Módulo de analítica: tiempos de ciclo y 7 KPIs de negocio
│   │   ├── landing/           # Landing comercial: Workflow 220vh, Ambient Tech y Ohm
│   │   ├── technician/        # Portal de técnico, mesa de trabajo y copiloto Ohm
│   │   └── tracking/          # Portal público de rastreo para clientes
│   ├── pages/                 # Páginas principales (Home, Login, Register, Portal, AdminAnalyticsPage, LandingPage)
│   ├── tests/                 # 170 tests con Vitest y Testing Library (24 suites)
│   ├── utils/                 # Constantes de estados, formateo de fechas, moneda, teléfono y PII
│   ├── App.css                # Estilos generales, Workbench y variables del tema OKLCH
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
    *   *Identidad del Asistente ("Ohm") & Feedback Dinámico:* Renombramiento integral a **Ohm** y agregado de temporizador en `AiChatDrawer.jsx` (>3.5s) que muestra `"Ohm está experimentando alta demanda, reintentando conexión..."` durante reintentos backend.
    *   *Fix RBAC SLA Config & Reintentos 503:* `GET /shops/sla-config` migrado a `subscription_guard` para habilitar lectura a técnicos de taller para el cálculo de badges SLA vencidos, y bucle de reintento con backoff (1s, 2s, 4s) ante 503 en `CorrectionService` y `ExplanationService`.
*   **Router de Modelos Ohm, Localización del Prompt y Blindaje de Tests (27 de Agosto, 2026):**
    *   *Router de Modelos:* Corrección del identificador de modelo rápido en `app/config.py` a `"gemini-3.5-flash-lite"`.
    *   *Localización del Prompt:* Especialización y traducción al español del system prompt de diagnóstico en `app/routers/diagnostic.py` (`workshop_diagnostic_chat`).
    *   *Dependencias:* Incorporación de `respx==0.23.1` y fijación determinística de `google-genai==1.2.0` en `requirements.txt`.
    *   *Fixtures y Mocks:* Inyección de `created_at=now` en el fixture de `Shop` de `test_dashboard_ticket_filters.py`, actualización de assert en `test_model_router.py`, y refactor de `FakeServerError503` en `test_gemini_503_retry.py` utilizando `requests.Response` real con `encoding="utf-8"`.
    *   *Verificación y Calidad:* **152 tests de backend** en Pytest (100% pasando) y **99 tests de frontend** en Vitest (100% pasando). Ciclo SDD archivado en `openspec/changes/archive/2026-08-27-ohm-router-and-test-suite-stabilization/`.
*   **Estabilización del Copiloto Ohm, Selector de Repuestos y Endpoint PATCH de Notas (27 de Agosto, 2026 - Tarde):**
    *   *Aislamiento de Contexto en Chat IA:* En `TechnicianDashboard.jsx`, se corrigió la limpieza de estado al cerrar `TechnicianWorkModal` reseteando `selectedTicketForAi(null)` y cerrando el drawer (`setIsAiDrawerOpen(false)`), evitando fuga de historial hacia otros tickets mientras el backend preserva el chat al reabrir el mismo equipo.
    *   *Soporte de Paginación en Repuestos:* En `PartsSelector.jsx`, se adaptó el consumo de `/inventory` extrayendo `data.items || data`, resolviendo el catálogo vacío en el selector de piezas del técnico.
    *   *Actualización Parcial de Tickets (Fix 405 Method Not Allowed):* Se implementó `update_ticket_partial` en `ticket_service.py` y se expuso `PATCH /tickets/{ticket_id}` en `routers/tickets.py` con el esquema `TicketUpdate`, permitiendo guardar notas técnicas y diagnósticas sin disparar mutaciones de estado automáticas a `ESPERANDO_APROBACION`.
*   **Refinamiento de Señales SLA y Badges de Excepción en AdminTicketCard (4 de Septiembre, 2026):**
    *   *Estandarización CSS:* Normalización de la clase `.badge-exception` en `App.css` conforme a `DESIGN.md` (display `inline-flex`, 6px border-radius, tipografía 12px con 500 font-weight).
    *   *Señales de Urgencia en Tarjeta:* Se incorporó el modificador visual `.is-stale` al contenedor de `.ticket-card` ante tickets con SLA vencido, tooltip accesible `title="Tiempo límite de atención superado (SLA vencido)"` con selector `data-testid="sla-stale-badge"`, y se eliminó la duplicidad del badge "Sin técnico" en la fila de señales. Suite actualizada en `AdminTicketCard.test.jsx`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-04-admin-card-sla-badge/`.
*   **Validación y Sanitización de Teléfonos Celulares Ecuatorianos (4 de Septiembre, 2026):**
    *   *Utilidad Centralizada:* Creación del módulo `src/utils/phone.js` con las funciones `isValidMobilePhone` (soporte para formato nacional `09XXXXXXXX` de 10 dígitos e internacional `+5939XXXXXXXX` / `5939XXXXXXXX`, permitiendo vacíos en campos opcionales) y `cleanPhoneNumber` (eliminación de espacios, guiones y paréntesis).
    *   *Integración en Intake de Órdenes:* Sustitución de la regex genérica en `NewTicketModal.jsx` por el validador estricto con mensaje de formato asistido, garantizando que el Smart Action CTA genere enlaces funcionales de WhatsApp click-to-chat. Suite de pruebas unitarias en `phone.test.js` y `NewTicketModal.test.jsx`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-04-ecuadorian-phone-validation/`.
*   **Componente Unificado StatusBadge en Admin y Portal de Técnico (4 de Septiembre, 2026):**
    *   *Componente Reutilizable:* Implementación de `<StatusBadge />` en `src/components/shared/StatusBadge.jsx`, consumiendo `STATUS_CONFIG` para color, fondo, bordes e iconos contextuales conforme a `DESIGN.md`, con soporte de variantes de tamaño (`sm`, `md`) y fallback tolerante a fallos para estados atípicos.
    *   *Paridad Estética entre Mesas de Trabajo:* Reemplazo de estilos inline dispersos en `AdminTicketCard.jsx` y migración de `.tech-status-pill` en `TechnicianTicketCard.jsx` hacia el componente unificado. Pruebas unitarias en `StatusBadge.test.jsx` e integración en `TechnicianPortal.test.jsx`. Ciclos SDD archivados en `openspec/changes/archive/2026-09-04-unified-status-badge/` y `openspec/changes/archive/2026-09-04-technician-status-badge/`.
*   **Sanitización y Validación Defensiva en Registro y Auth (7 de Septiembre, 2026):**
    *   *Frontend:* Normalización de entrada de WhatsApp en `RegisterPage.jsx` con `cleanPhoneNumber` y validación estricta con `isValidMobilePhone`.
    *   *Backend:* Sanitización en `RegisterRequest` (`app/schemas/auth.py`) con validador Pydantic v2 que convierte cadenas vacías o compuestas sólo de espacios en blanco a `None`, y valida formato celular ecuatoriano en números no nulos. Ciclo SDD archivado en `openspec/changes/archive/2026-09-07-register-whatsapp-sanitization/`.
*   **Sanitización de Repuestos en Inventario (7 de Septiembre, 2026):**
    *   *Backend:* Validador Pydantic `@field_validator("name")` en `InventoryCreate` e `InventoryUpdate` (`app/schemas/inventory.py`), aplicando `strip()` y forzando una longitud mínima de 2 caracteres reales no-blancos para rechazar entradas espurias. Pruebas unitarias en `backend/tests/unit/test_inventory_schemas.py`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-07-inventory-name-sanitization/`.
*   **Normalización de Correo en Inicio de Sesión (7 de Septiembre, 2026):**
    *   *Frontend:* En `LoginPage.jsx`, aplicación de `email.trim().toLowerCase()` antes de la invocación de autenticación, previniendo rechazos de credenciales por mayúsculas automáticas del teclado en dispositivos móviles o espacios en blanco residuales. Pruebas unitarias añadidas en `frontend/src/tests/pages/LoginPage.test.jsx`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-07-login-email-sanitization/`.
*   **Sanitización de Datos de Técnicos en Backend (7 de Septiembre, 2026):**
    *   *Backend:* Validadores Pydantic en `TechnicianCreate` y `TechnicianUpdate` (`app/schemas/technician.py`) aplicando `strip()`, exigiendo al menos 2 caracteres no-blancos en `full_name` y convirtiendo `contact` y `declared_specialty` compuestos de solo espacios en `None`. Pruebas en `backend/tests/unit/test_technician_schemas.py`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-07-technician-data-sanitization/`.
*   **Sanitización de Campos Descriptivos en Tickets/Órdenes (7 de Septiembre, 2026):**
    *   *Backend:* Validadores Pydantic en `TicketCreate`, `TicketUpdate` y `TicketDiagnosticUpdate` (`app/schemas/ticket.py`) que recortan espacios en blanco (`strip()`) en `device_brand`, `device_model`, `issue_description` (exigiendo >= 2 caracteres útiles), sanean datos de cliente (`customer_name`, `customer_phone` con validación de móvil ecuatoriano) y normalizan notas técnicas. Pruebas en `backend/tests/unit/test_ticket_schemas.py`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-07-ticket-data-sanitization/`.
*   **Generación y Edición de Diagnósticos Asistidos por Ohm (7 de Septiembre, 2026):**
    *   *Backend & Base de Datos:* Añadida columna `draft_diagnostic` en modelo `Ticket` con migración Alembic `e5f6a7b8c9d0`. Endpoints `POST /tickets/{id}/generate-diagnostic` (gating estricto: estados `EN_REPARACION` o `LISTO_PARA_RETIRAR`, rechazo HTTP 400 por estado inválido o chat vacío con Ohm, HTTP 409 por regeneración si ya existe borrador) y `POST /tickets/{id}/apply-diagnostic` con payload opcional `ApplyDiagnosticRequest(edited_diagnostic: str | None)` para aplicar borrador directamente o con ajustes manuales del técnico.
    *   *Frontend & UX:* Sección de borrador editable en `TechnicianWorkModal.jsx`, permitiendo revisión técnica previa a la persistencia en `diagnostic_notes` y notificación al cliente. Pruebas unitarias en `test_diagnostic_generation.py` y `TechnicianPortal.test.jsx`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-07-ohm-generate-diagnostic-flow/`.
*   **Autorización de Ingreso de Equipos por Técnicos — Flag por Shop (7 de Septiembre, 2026):**
    *   *Backend & Base de Datos:* Añadida columna `allow_technician_intake` en modelo `Shop` (default `False`, opt-in) con migración Alembic `f6a7b8c9d0e1`.
    *   *Seguridad & Control de Acceso:* Implementación del guard `verify_can_create_ticket` en `app/core/dependencies.py` para `POST /tickets` (permite admins siempre, técnicos solo si la tienda tiene el flag activo; deniega resto con HTTP 403). Atribución en `TicketStatusHistory` registrando al técnico como autor del ingreso inicial.
    *   *Endpoints de Configuración:* Endpoints `GET /shops/settings` y `PATCH /shops/settings` (exclusivo para `admin`), y exposición de `allow_technician_intake: bool` en `GET /technicians/me` (`TechnicianMeResponse`).
*   **Ohm en el Panel de Administrador — Asistente Conversacional Stateless (8 de Septiembre, 2026):**
    *   *Arquitectura & Catálogo Cerrado de Intents:* Implementación de un pipeline determinista y seguro para consultas administrativas sin riesgo de SQL injection ni ejecución arbitraria. Catálogo cerrado v1: `ganancias_del_dia` (suma de `total_cost` de tickets listos hoy), `equipos_ingresados_hoy` (conteo de tickets creados hoy) y `equipos_sin_tocar` (equipos activos sin cambio de estado por >48h), con clasificación mediante coincidencia directa rápida o fallback con `gemini-3.5-flash-lite`, y respuesta enlatada ante consultas fuera del catálogo.
    *   *Backend & Seguridad:* Nuevo endpoint `POST /admin/assistant/query` protegido con `admin_guard` en `backend/app/routers/admin_assistant.py` y capa de servicios en `admin_assistant_service.py`. Aislamiento multi-tenant estricto con `shop_id`.
    *   *Frontend & UX:* Adaptación de `AiChatDrawer.jsx` con prop `context="admin"` para mostrar chips rápidos (💰 Ganancias de hoy, 📥 Equipos ingresados hoy, ⏱️ Equipos sin tocar), ocultando controles de diagnóstico/RAG de técnicos. Integración de `AiChatBubble` y `AiChatDrawer` en `AdminDashboard.jsx`.
*   **Refinamiento Comercial del Dashboard de Administrador (8 de Septiembre, 2026):**
    *   *Frontend & UX:* Refactor de la barra de acciones de la mesa de trabajo (`workbench-toolbar`) en `AdminDashboard.jsx` organizando el flujo operativo en 4 bloques limpios: Búsqueda con ícono `<Search />` y placeholder descriptivo (`.search-input-wrapper`), filtros de fecha con selector y botón de actualización (`<RotateCw />`), switcher de vista (`Lista` / `Kanban`), y botón de acción principal prioritario `+ Nuevo equipo` con ícono `<Plus />` (`.toolbar-cta-btn`). Unificación del copywriting de creación a `+ Nuevo equipo` tanto en toolbar como en el `nav-pill`.
    *   *Verificación y Calidad:* 149 tests pasando en 20 suites de Vitest (100%), build de producción con Vite exitoso.
*   **Blindaje de Ohm — Scope Técnico y Anti Prompt-Injection (8 de Septiembre, 2026 - Tarde):**
    *   *Base de Datos & Modelo:* Creación de la tabla `ai_security_events` con el modelo `AiSecurityEvent` (`id`, `shop_id`, `technician_id`, `ticket_id`, `event_type`, `message_excerpt` limitado a 280 caracteres, `created_at`) y migración Alembic `d1e2f3a4b5c6_add_ai_security_events.py` aplicada exitosamente.
    *   *Servicio de Seguridad (`ai_safety_service.py`):* Pre-clasificador ultrarrápido con `gemini-3.5-flash-lite` (`classify_message_safety`) que evalúa `on_topic` y `injection_attempt` en una sola llamada JSON antes de tocar modelos de razonamiento caros o el pipeline RAG. Política fail-open ante caídas externas para evitar bloqueo del técnico.
    *   *Respuesta Enlatada Unificada:* Respuesta estándar neutra (`CANNED_REDIRECT_RESPONSE`) idéntica tanto para off-topic como para inyecciones, evitando dar feedback útil a atacantes sobre la detección.
    *   *Hardening del Prompt (Sandwich Defense):* Inclusión de instrucciones estrictas de inmunidad (`ANTI_INJECTION_SYSTEM_INSTRUCTION`) al inicio del prompt y recordatorio de cierre (`SANDWICH_PROMPT_REMINDER`) tras el mensaje del usuario para maximizar el peso atencional en Gemini 3.6 Flash.
    *   *Integración en Endpoints:* Intercepción en los dos flujos de entrada de Ohm: `POST /diagnostic/chat` (`workshop_diagnostic_chat`) y `POST /tickets/{id}/diagnostic-chat` (`CorrectionService.handle_chat_message`).
*   **Sanitización de Consultas y Búsquedas en Backend (9 de Septiembre, 2026):**
    *   *Backend & Servicios:* Normalización defensiva con `.strip()` y coerción a `None` ante cadenas vacías o compuestas exclusivamente de espacios en blanco para los parámetros de búsqueda en `ticket_service.list_tickets` (`GET /tickets`), `list_inventory` (`GET /inventory`, sanitizando tanto `search` como `sku`), y `ClientService.get_clients` / `get_clients` (`GET /clients`).
    *   *Resolución de Defectos:* Elimina el falso negativo donde un término con espacios o solo espacios (`"   "`) generaba condiciones `ilike("%   %")` que filtraban erróneamente todos los registros devolviendo listas vacías, y asegura que búsquedas por UUID en tickets reconozcan el identificador limpio sin fallar por espacios residuales de portapapeles.
    *   *Verificación y Calidad:* Suite de pruebas unitarias dedicada en `backend/tests/unit/test_search_sanitization.py` (4 tests cubriendo casos de espacios puros, términos acolchados y búsqueda exacta por UUID). Ciclo SDD archivado en `openspec/changes/archive/2026-09-09-backend-search-sanitization/`.
*   **Optimización de Ergonomía Desktop y Contraste OKLCH de Tarjetas (9 de Septiembre, 2026 - Tarde):**
    *   *Contenedor Workbench en Desktop:* Restricción del contenedor principal `.workbench-canvas` a `max-width: 1500px; margin: 0 auto;` en `frontend/src/App.css`, previniendo dispersión visual horizontal y estiramiento desproporcionado de tarjetas KPI en monitores de alta resolución, manteniendo intacto el padding lateral (`32px`) y todas las media queries responsive para mobile y tablet.
    *   *Separación Visual Tarjeta / Fondo:* Reemplazo del background en `.ticket-card` y `.tech-ticket-card` de `var(--bg-paper)` a `var(--bg-surface)` para lograr un salto de luminosidad nítido dentro del sistema OKLCH frente al contenedor (`var(--bg-paper)`): elevación de +5% en modo oscuro (`oklch(25% 0.02 260)` vs `20%` del canvas y `16%` del fondo general), y contraste sutil en modo claro (`oklch(91% 0.015 75)` frente a `94%` del canvas y `97%` de la página).
    *   *Elevation Box-Shadow:* Incorporación de sombras sutiles estratificadas: `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)` en modo claro (`[data-theme="light"]`) y `box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25), 0 1px 2px rgba(0, 0, 0, 0.15)` en modo oscuro.
    *   *Verificación y Calidad:* 149 tests pasando al 100% en 20 suites de Vitest, preservando border-radius, padding y gaps de grilla. Ciclo SDD archivado en `openspec/changes/archive/2026-09-09-workbench-desktop-contrast/`.
*   **Ruta Dedicada de Métricas y Motor de 7 KPIs Ejecutivos de Negocio (11 de Septiembre, 2026):**
    *   *Arquitectura de Ruta y Feature-Gating (ADR-001):* Extracción de la analítica del taller fuera del modal embebido de `AdminDashboard.jsx` hacia una ruta dedicada `/admin/metricas` (`AdminAnalyticsPage.jsx`). Esto desacopla el workbench de despacho diario de alta frecuencia del reporting ejecutivo y prepara la plataforma para feature gating declarativo por plan/tiers sin contaminar componentes operacionales.
    *   *Motor de Analítica de Negocio (ADR-002 & 7 KPIs):* Implementación de la función `get_workshop_business_insights` en `ticket_service.py` calculando:
        1. *Ranking de Marcas y Modelos:* Distribución de equipos admitidos y desglose de top modelos por fabricante.
        2. *Tasa de Reparación Confirmada:* Efectividad de conversión por marca (`EN_REPARACION`, `ESPERANDO_REPUESTO`, `LISTO_PARA_RETIRAR`), aplicando la regla de negocio estricta donde el denominador excluye tickets en estado `NO_APROBADO` (`valid_intake = total - rejected`).
        3. *Rotación de Repuestos:* Piezas e insumos más utilizados con ingresos generados y cruce de stock en inventario.
        4. *Fidelidad de Clientes (2+ Equipos):* Tasa de recurrencia global y listado de clientes frecuentes con enmascaramiento estricto de PII (`maskPhone`, `maskEmail`).
        5. *Rendimiento de Técnicos:* Productividad en banco técnico (resueltos `LISTO_PARA_RETIRAR` vs activos en banco y tasa de completitud).
        6. *Estructura de Margen Bruto:* Comparativa de ingresos por mano de obra vs repuestos, costo de adquisición de piezas e indicador de margen bruto neto estimado.
        7. *Alertas de Repuestos Críticos:* Identificación automática de repuestos de alta rotación con stock igual o inferior al umbral mínimo (`low_stock_alert`) o agotados.
    *   *Backend & Seguridad:* Nuevo endpoint `GET /tickets/analytics/business-insights` protegido por `admin_guard`, declarado antes de `/{ticket_id}` para evitar colisiones de ruta UUID. Esquemas tipados `BusinessInsightsResponse` en `app/schemas/ticket.py`. Aislamiento multi-tenant por `shop_id` y exclusión de tickets `NO_APROBADO` del cómputo de piezas y facturación.
    *   *Frontend & UX:* Componente `BusinessInsightsView.jsx` integrado con TanStack Query (stale time 2 min), selector de períodos (7, 30, 90 días), barras de progreso segmentadas de margen y tablas de alta densidad. `AdminAnalyticsPage.jsx` estructurado con 2 subpestañas accesibles (`tablist`/`tab`): *Tiempos de Ciclo y SLA* y *Flota, Repuestos y Clientes*. Estilos OKLCH responsive en `analytics.css`.
    *   *Verificación y Calidad:* **185 tests de backend** pasando al 100% (incluyendo pruebas unitarias dedicadas en `test_business_insights_analytics.py` y pruebas de integración REST en `test_business_insights_api.py`) y **155 tests de frontend** pasando al 100% en 21 suites de Vitest (con suite completa de tabs y KPIs en `AdminAnalyticsPage.test.jsx`).
*   **Landing Page Comercial — Workflow Scroll-Driven de 4 Etapas (Fase 2.5) (17 de Septiembre, 2026):**
    *   *Scroll-Driven Interactivo:* Implementación de track de 220vh en desktop (`LandingWorkflowDemo.jsx` y `landing.css`) con posicionamiento sticky y avance natural del ciclo de vida del taller (`01 Recibido` → `02 Diagnóstico` → `03 Aprobación` → `04 Listo`).
    *   *Doble Modalidad de Interacción:* Sincronización bidireccional perfecta entre desplazamiento por scroll y selección manual por pestañas (*tabs*) accesibles (`role="tab"`), calculando offset de desplazamiento con compensación de barra de navegación para evitar saltos bruscos.
    *   *Fidelidad Técnica del Workbench:* Sustitución de filas genéricas por tarjetas operativas elevadas con estética Workbench OKLCH, visualización de SLA perimetral, diagnóstico con desglose de multímetro y repuestos, flujo de aprobación de presupuesto por WhatsApp y retiro del equipo con evidencia fotográfica.
    *   *Panel Derecho Contextual:* Transformación del panel secundario en una tarjeta de valor que explica el beneficio operativo directo de cada etapa para el dueño del taller.
    *   *Mobile First Resiliente:* Desactivación del sticky en móviles y tablets (<960px) en favor de pestañas táctiles horizontales sin scroll-driven artificial ni layout shifts.
*   **Landing Page Comercial — Ambient Tech Dinámico Global & Toast Sileo (Fase 2.7) (17 de Septiembre, 2026):**
    *   *Red Neuronal de Partículas en Canvas:* Componente ambiental unificado [`LandingAmbientTech.jsx`](file:///frontend/src/features/landing/components/LandingAmbientTech.jsx) con fondo tecnológico dinámico de nodos y enlaces que nacen y mueren orgánicamente por proximidad, desacoplado de CSS keyframes estáticos.
    *   *Modulación Narrativa de Intensidad:* Sistema reactivo a la posición de scroll que modula suavemente (lerp) la opacidad y velocidad de la red según la sección activa (Hero al 40%, Problema al 20%, Workflow al 35%, Ohm al 45%, Piloto al 30%).
    *   *Densidad Calibrada & Ergonomía:* Nodos optimizados por dispositivo (30–40 en desktop, 22–28 en tablet, 12–18 en mobile) para garantizar una atmósfera tecnológica viva que no compite con la legibilidad del contenido.
    *   *Notificación de Conversión Sileo:* Integración de `LandingToastProvider.jsx` reutilizando la librería Sileo, activado mediante trigger híbrido por intención/scroll con persistencia en `sessionStorage` para evitar spam, enlazando al formulario de postulación del Programa Piloto.
    *   *Accesibilidad y Rendimiento:* Detección nativa de `prefers-reduced-motion` que renderiza una constelación estática sin bucle `requestAnimationFrame`, y limpieza estricta de memoria al desmontar.
*   **Landing Page Comercial — Experiencia Interactiva de Ohm (Fase 3) (17 de Septiembre, 2026):**
    *   *Estación de Diagnóstico en Mesón:* Reconstrucción de [`LandingOhm.jsx`](file:///frontend/src/features/landing/components/LandingOhm.jsx) pasando de una tarjeta densa y pasiva a una estación de trabajo interactiva de 4 etapas:
        1. *01 Consulta Técnica:* Registro de caso en mesón (MacBook Air M1, placa 820-02016, línea PP3V3_S2 con 0.8V).
        2. *02 Memoria del Taller:* Coincidencias con histórico previo del taller (Ticket #TK-7412 con 91% de similitud y #TK-6201 con sulfatación en pin 4 de U7700).
        3. *03 Mediciones / Hallazgos:* Comparativa de multímetro en banco (~450Ω esperados vs 12Ω en corto medidos en banco).
        4. *04 Sugerencia Técnica:* Procedimiento ordenado de 3 puntos (desoldar C3104, inspección de U7700 con alcohol isopropílico, prueba de encendido) con tiempo histórico estimado de ~40 min.
    *   *Capitalización en Memoria del Taller:* Bloque visual explícito que evidencia cómo la resolución técnica confirmada se persiste en el historial privado del taller para alimentar futuras consultas de todo el equipo.
    *   *Privacidad y Aislamiento Factual:* Copy estricto validado: *"Los datos de cada taller permanecen aislados de otros talleres. Ohm utiliza el historial disponible del propio taller para sus consultas."*
    *   *Navegación y Ergonomía:* Stepper superior accesible con touch targets de 44px, navegación secuencial (*Anterior* / *Siguiente etapa* / *Reiniciar recorrido*), indicadores de progreso por puntos y altura calibrada (`min-height: 420px`) para erradicar el *layout shift*.
    *   *Verificación y Calidad:* **164 tests de frontend** pasando al 100% en 23 suites de Vitest, build de producción exitoso (2.40s) y validación visual headless CDP en resoluciones 1920x1080, 1440x900, 1366x768, 390x844 y 412x915 sin desbordes horizontales.

*   **Sanitización de Búsqueda de Clientes (14 de Septiembre, 2026):**
    *   *Backend & Servicios:* Normalización defensiva con `.strip()` y coerción a `None` para cadenas vacías o compuestas exclusivamente de espacios en blanco en el parámetro `search` de `ClientService.get_clients` (`GET /clients`) y `backend/app/routers/clients.py`.
    *   *Resolución de Defectos:* Elimina falsos negativos donde búsquedas de clientes con espacios o padding residual devolvían colecciones vacías. Suite de pruebas unitarias en `backend/tests/unit/test_search_sanitization.py`. Ciclo SDD archivado en `openspec/changes/archive/2026-09-14-sanitize-client-search/`.
*   **Gateway LLM Resiliente, Fallback a OmniRoute y Logging de Truncamiento (15 de Septiembre, 2026):**
    *   *Backend & Arquitectura:* Creación del módulo centralizado `backend/app/services/llm_gateway.py` (`generate_llm_content`, `LLMResult`, `LLMGatewayError`) para desacoplar las llamadas de IA de los servicios de negocio.
    *   *Enrutamiento por Tiers:* Soporte para tier `"fast"` (`gemini-3.5-flash-lite`, 320 tokens) y `"reasoning"` (`gemini-3.6-flash`, 700 tokens base).
    *   *Fallback a OmniRoute:* Tolerancia a fallos automática hacia proxy compatible con OpenAI (`OmniRoute`) ante errores 429 (Resource Exhausted), 503 o timeouts de Gemini primario, utilizando combos configurables (`OMNIROUTE_FAST_COMBO`, `OMNIROUTE_REASONING_COMBO`).
    *   *Detección Preventiva de Truncamiento:* Inspección de `response.candidates[0].finish_reason` en Gemini y `finish_reason == "length"` en OmniRoute; emisión de advertencia estructurada `logger.warning` con evento `llm_max_tokens_reached` para detectar agotamiento de tokens antes de reportes en producción. Pruebas unitarias en `backend/tests/unit/test_llm_gateway.py`.
*   **Búsqueda Web Técnica (Tavily) & Deep Research en Copiloto Ohm (15 de Septiembre, 2026):**
    *   *Backend & Integración Externa:* Creación de `backend/app/services/tavily_service.py` (`search_technical_web`) consumiendo la API de Tavily con timeout estricto (`TAVILY_TIMEOUT_SECONDS = 2.5`), recuperando diagramas de carga, esquemáticos y soluciones de comunidades técnicas.
    *   *Contrato de Datos:* Parámetro `deep_research: bool = False` en `DiagnosticMessageIn`, inyección estructurada de hallazgos verificados en el prompt de Ohm (`web_context_prompt`) y retorno de `sources` (título y URL) anexado al pie del mensaje.
    *   *Frontend & UX:* Switch/selector de modo de razonamiento en `AiChatDrawer.jsx` (`sendMode === "reasoning"`), permitiendo al técnico activar la búsqueda técnica web con renderizado interactivo de las fuentes citadas. Pruebas unitarias e integración en `test_tavily_service.py` y `test_diagnostic_chat_router.py`.
*   **Landing Page V2 Comercial Orientada a Conversión (15-16 de Septiembre, 2026):**
    *   *Optimización Mobile P0:* Compactación vertical del Hero en viewports <640px garantizando visibilidad inmediata del headline, la oferta de lanzamiento ("$0 Primer Mes / 100% Bonificado") y el CTA principal dentro del primer viewport en dispositivos 360x800 y 390x844.
    *   *Navbar Adaptativa <380px:* Eliminación de tensiones horizontales y prevención de desbordes en pantallas pequeñas de 360px manteniendo legibilidad y acceso a controles.
    *   *Sección de Resultados Cualitativos:* Creación del componente `LandingQualitativeResults.jsx` destacando el impacto operativo directo en los talleres.
    *   *Ajuste de Contraste en Modo Claro:* Refinamiento de tokens OKLCH y contraste visual en elementos interactivos y badges destacados (como la burbuja de "PROGRAMA PILOTO EXCLUSIVO") en `landing.css`.
*   **Calibración de Tokens y Timeout Aislado para Deep Research (16 de Septiembre, 2026):**
    *   *Resolución de Truncamiento:* Elevación de `chosen_max_tokens` a **1500** para llamadas con `deep_research=True` en `correction_service.py:135`, mitigando el agotamiento de presupuesto provocado por los tokens de pensamiento interno (`thinking_process`) de Gemini 3.6 Flash.
    *   *Timeout Aislado:* Adición de `gemini_deep_research_timeout_seconds: float = 22.0` en `app/config.py` y soporte de `timeout_seconds` opcional en `generate_llm_content`, desacoplando el flujo de investigación web del timeout general de 8.0s (`gemini_primary_timeout_seconds`) y previniendo cancelaciones espurias por `asyncio.wait_for`.
    *   *Suite de Tests:* Pruebas unitarias en `test_deep_research_tokens.py` y `test_llm_gateway.py` validando la inyección de 1500 tokens, timeout de 22.0s y logging del warning de `MAX_TOKENS`.
*   **Calibración de Tokens de Razonamiento Base (1500 tokens) y Timeout Primario (12.0s) (17 de Septiembre, 2026):**
    *   *Resolución Estructural de Truncamiento:* Elevación de `gemini_reasoning_max_output_tokens` de 700 a **1500** en `app/config.py` y `ModelRouter`, dotando al tier `"reasoning"` base (sin búsqueda web) del margen suficiente para que el `thinking_process` de Gemini 3.6 Flash no agote el presupuesto en consultas técnicas complejas sobre multímetro, líneas de voltaje y PMIC.
    *   *Calibración del Timeout Primario:* Aumento de `gemini_primary_timeout_seconds` de 8.0s a **12.0s** en `app/config.py`, otorgando margen seguro a los tiempos observados (9.37s) en razonamiento puro sin afectar al tier `"fast"` (<3s) ni entrar en conflicto con el timeout aislado de Deep Research (`GEMINI_DEEP_RESEARCH_TIMEOUT_SECONDS = 22.0`).
    *   *Suite de Tests:* Pruebas en `test_deep_research_tokens.py` y `test_model_router.py` certificando la preservación de 1500 tokens y 12.0s en el flujo de chat estándar de razonamiento.
*   **Subfase 3.1 — Fidelidad Conversacional de Ohm en Landing Page (18 de Septiembre, 2026):**
    *   *Etapa 02 Memoria Técnica en Chat:* Transformación de la etapa 02 en `LandingOhm.jsx` para reflejar con fidelidad la experiencia real de `AiChatDrawer`. La recuperación histórica se modeló como una cita conversacional estructurada en el diálogo de Ohm (#TK-7412: falla PP3V3_S2 por capacitor C3104 en corto y sulfatación en pin 4 de U7700).
    *   *Eliminación de Métricas Ficticias:* Erradicación del porcentaje numérico "91%" y del caso secundario #TK-6201, reemplazándolos por un badge cualitativo de coincidencia técnica verificada en el mesón de trabajo.
    *   *Deep Linking y Navegación:* Soporte para anclaje por URL hash (`#ohm-demo`) y navegación fluida entre etapas de la demo interactiva.
*   **Subfase 3.2 — Paridad UX Admin/Técnico, Selector de 7 Estados en Detalle y Consolidación de Modales (18 de Septiembre, 2026):**
    *   *Selector Administrativo de Estados en Detalle:* Integración en `TicketDetailModal.jsx` de un selector para los 7 estados administrativos (`ADMIN_STATUSES`) ubicado en la barra de estado bajo el header, con componente reactivo `<StatusBadge />`, mutación atómica `PATCH /tickets/{id}/status` y propagación de `onStatusChange`.
    *   *Consolidación de Modales y Reducción de Deuda Técnica:* Reemplazo del modal inline duplicado en `AdminTicketCard.jsx` (eliminando más de 360 líneas de código redundante) por la instancia unificada y reutilizable de `TicketDetailModal.jsx`.
    *   *Sincronización Bidireccional con Kanban y Tarjetas:* Mantenimiento reactivo del estado seleccionado (`selectedStatus`) tanto en la tarjeta de lista como en las 5 columnas operativas del tablero Kanban (`KanbanBoard.jsx`).
    *   *Preservación del Modelo Operativo:* Separación intacta entre permisos y capacidades de Admin (7 estados, notas, diagnóstico, piezas de solo lectura) y Técnico (`TechnicianWorkModal`, flujo no lineal enfocado en banco de trabajo).
    *   *Auditoría Visual y Tests:* Creación de suite dedicada `TicketDetailModal.test.jsx` (4 tests), test de integración en `AdminTicketCard.test.jsx`, alcanzando **170 tests pasando al 100% en 24 suites de Vitest** y auditoría visual de 9 capturas en múltiples resoluciones desktop y mobile (`frontend/screenshots/phase-3.2/`).
*   **Landing Page Comercial — Estación de Diagnóstico Ohm & Microinteracciones React Bits (Fase 3) (18 de Septiembre, 2026):**
    *   *Estación de Diagnóstico en Mesón:* Reconstrucción integral de [`LandingOhm.jsx`](file:///frontend/src/features/landing/components/LandingOhm.jsx) evolucionando el módulo hacia una estación interactiva de diagnóstico técnico estructurada en 4 etapas:
        1. *01 Consulta Técnica:* Registro de caso en mesón (MacBook Air M1, placa 820-02016 tras derrame, línea PP3V3_S2 en 0.8V vs 3.3V).
        2. *02 Memoria del Taller:* Coincidencia del 91% con caso previo resuelto (#TK-7412: corto en capacitor cerámico C3104 tras derrame) y referencia secundaria en la misma placa (#TK-6201: sulfatación en pin 4 de U7700), evidenciando la memoria acumulativa del taller.
        3. *03 Mediciones / Hallazgos:* Comparativa de multímetro en banco (~450Ω esperados vs 12Ω en corto parcial medidos en circuito).
        4. *04 Sugerencia Técnica:* Procedimiento ordenado de 3 pasos (desoldar C3104, inspección de pines de U7700 con alcohol isopropílico 99%, prueba de encendido) con tiempo histórico estimado (~40 min), disclaimer de decisión técnica (*«⚖️ La decisión final permanece en manos del técnico»*) y banner de capitalización en la memoria técnica del taller.
    *   *Patrones de React Bits de Forma Nativa (0 Dependencias Nuevas):* Implementación con React 19 y Vanilla CSS OKLCH sin librerías externas:
        1. *Stepper:* Pestañas accesibles con `role="tablist"`, `role="tab"`, `aria-selected`, `aria-controls`, navegación por teclado (`ArrowRight`, `ArrowLeft`, `Home`, `End`), touch targets $\ge 44\text{px}$ y numeración en JetBrains Mono.
        2. *Border Glow:* Pulsación continua de 8s (`@keyframes ohmBorderGlow`) oscilando el borde y resplandor con tokens `var(--color-accent)` sin efecto neón.
        3. *Spotlight Card:* Seguimiento del cursor en coordenadas locales (`--spotlight-x`, `--spotlight-y`) con degradado radial (`radial-gradient(380px circle...)`), desactivado en pantallas táctiles (`@media (hover: none)`).
    *   *Privacidad y Aislamiento Factual:* Garantía en el footer con copy estricto: *"🔒 Los datos de cada taller permanecen aislados de otros talleres. Ohm utiliza el historial disponible del propio taller para sus consultas."*
    *   *Ergonomía, Rendimiento y A11y:* Altura estable (`min-height: 420px`) para evitar layout shift, soporte de `prefers-reduced-motion` y verificación visual responsive en desktop y mobile (1920x1080, 1440x900, 1366x768, 390x844 y 412x915) sin desbordes horizontales.

### 6.2 Estado del Workbench, Portal de Técnico, Asistente Ohm y Landing Page
*   **Módulo Workbench, Portal de Técnico, Asistente Ohm, Analítica Ejecutiva, Landing Page Comercial V2 y Gateway LLM Resiliente:** 100% implementados, respaldados por testing automatizado (**170 tests de frontend en 24 suites** y **243 tests de backend**), blindaje multi-tenant, sanitización multi-capa en todos los flujos de entrada y parámetros de búsqueda, ergonomía visual desktop calibrada a 1500px, elevación OKLCH y sombras de contraste en tarjetas, enrutamiento por roles, asistente conversacional para admins con catálogo cerrado, blindaje de seguridad y anti-injection en el copiloto Ohm, gateway LLM desacoplado con fallback a OmniRoute, búsqueda técnica web con Tavily, calibración de tokens y timeouts de razonamiento, ruta dedicada de analítica `/admin/metricas` con motor de 7 KPIs de negocio y tiempos de ciclo (ADR-001 y ADR-002), Landing Page comercial de alta conversión V2 con Workflow scroll-driven de 220vh, Ambient Tech de partículas dinámicas global en Canvas, toast contextual Sileo, Estación Interactiva de Diagnóstico Ohm con fidelidad conversacional y memoria técnica de taller, y consolidación modular del detalle administrativo con selector de 7 estados y sincronización reactiva al Kanban.



