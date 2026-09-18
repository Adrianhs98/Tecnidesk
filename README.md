# TecniDesk

Micro SaaS multi-tenant para la gestión integral de talleres de reparación de celulares.

TecniDesk centraliza el ingreso de equipos, gestión de clientes, órdenes de servicio, diagnósticos técnicos asistidos por IA, inventario de repuestos, evidencias fotográficas, presupuestos y seguimiento público para clientes. Cada taller opera de forma estrictamente aislada mediante su identificador único (`shop_id`) y ofrece a sus clientes un portal de rastreo público con whitelabeling dinámico (logotipo y nombre propio).

---

## Funcionalidades Principales

### 🛠️ Workbench Operativo (Mesa de Trabajo de Alta Eficiencia)
- **Alternador de Vistas (Lista & Kanban):** Visualización en lista tabular paginada o tablero interactivo Kanban organizado en 5 columnas operativas (*Ingreso / Recepción*, *En Revisión & Diagnóstico*, *Presupuesto & Espera*, *En Reparación*, *Listo para Retirar*) con persistencia de preferencia en `localStorage`.
- **Consolidación de Modal de Detalle y Selector de 7 Estados (`TicketDetailModal`):** Unificación del detalle administrativo en `TicketDetailModal.jsx` erradicando modales duplicados en `AdminTicketCard`, con selector directo de los 7 estados (`ADMIN_STATUSES`) integrado en cabecera, mutación reactiva `PATCH /tickets/{id}/status` y sincronización bidireccional automática con la vista de Lista y el tablero Kanban.
- **Ordenamiento SQL Inteligente:** Priorización en backend mediante `CASE` que ubica al inicio tickets sin técnico asignado, seguidos de aquellos con SLA vencido y finalmente por orden cronológico.
- **Smart Action CTA:** Botón de acción rápida contextual (*Asignar* → *Diagnosticar* → *WhatsApp* → *Ver detalle*) para guiar al técnico hacia la acción prioritaria inmediata.
- **Badges de Estado Unificados (`<StatusBadge />`):** Estandarización visual de estados en tarjetas y modales conforme a `DESIGN.md`, con tokens de color, fondo, borde e iconos contextuales compartidos entre Admin y Portal de Técnico.
- **Señales SLA Visibles y Accesibles:** Alertas visuales perimetrales (`.is-stale`) y tooltips explicativos para tickets que exceden el tiempo máximo de atención en mostrador.
- **Guardia Estricta de Asignación Técnica:** Validación estricta que prohíbe la transición a `EN_REPARACION` si el ticket no cuenta con un técnico asignado (`UnassignedTechnicianError` / HTTP 400).
- **Auditoría Inmutable de Estados:** Registro síncrono en `ticket_status_history` de cada transición de estado con autor, timestamp y motivo.
- **SLAs Dinámicos y Multi-Tenant:** Umbrales de SLA configurables por cada taller (`shops.sla_config`) con panel de ajustes en tiempo real y fallback automático a defaults del sistema.
- **Analítica de Tiempos de Ciclo y Cuellos de Botella:** Endpoint y modal interactivo (`GET /tickets/analytics/cycle-times`) para monitorear Lead Time promedio, Cycle Time activo, desglose por etapa, porcentaje de cumplimiento de SLA y detección automática de cuellos de botella.
- **Ergonomía Desktop Calibrada (1500px):** Contenedor centralizado (`.workbench-canvas`) optimizado para evitar dispersión horizontal en pantallas panorámicas, preservando la adaptabilidad fluida en tablets y móviles.

### 📊 Analítica Operativa y KPIs Ejecutivos de Negocio (`/admin/metricas`)
- **Arquitectura de Ruta Dedicada (ADR-001):** Desacoplamiento total del workbench operativo de despacho diario mediante una vista dedicada `/admin/metricas` (`AdminAnalyticsPage`), lista para feature-gating declarativo sin sobrecargar componentes de intake.
- **Tiempos de Ciclo y Detección de Cuellos de Botella:** Pestaña especializada (`GET /tickets/analytics/cycle-times`) con cálculo de Lead Time promedio, Cycle Time activo en banco, desglose de permanencia por etapa y porcentaje de cumplimiento SLA contra umbrales personalizados del taller.
- **Motor de 7 KPIs Ejecutivos de Negocio (ADR-002):** Pestaña "Flota, Repuestos y Clientes" (`GET /tickets/analytics/business-insights`):
  1. *Ranking de Marcas y Modelos:* Volumen de admisión por fabricante con desglose de sus modelos principales.
  2. *Tasa de Reparación Confirmada:* Efectividad de conversión por marca (`EN_REPARACION`, `ESPERANDO_REPUESTO`, `LISTO_PARA_RETIRAR`) excluyendo del denominador los tickets rechazados (`NO_APROBADO`).
  3. *Repuestos con Mayor Rotación:* Ranking de componentes más consumidos, frecuencia de uso, facturación y cruce de existencias en tiempo real.
  4. *Fidelidad de Clientes (2+ Equipos):* Tasa de recurrencia del taller y listado de clientes leales con enmascaramiento defensivo de PII (`maskPhone`, `maskEmail`).
  5. *Rendimiento de Técnicos:* Seguimiento de productividad técnica (equipos resueltos `LISTO_PARA_RETIRAR` vs en banco y tasa de completitud).
  6. *Estructura de Margen Bruto:* Desglose financiero de ingresos por mano de obra vs repuestos, costo de adquisición y rentabilidad neta estimada.
  7. *Alertas de Repuestos Críticos:* Monitoreo proactivo de piezas de alta rotación con existencias en o por debajo del umbral mínimo de seguridad (`low_stock_alert`) o agotadas.
- **Selectores de Período y Caché Inteligente:** Filtros temporales en 7, 30 y 90 días gestionados concurrentemente mediante TanStack React Query con política `staleTime: 2 min`.

### 👨‍🔧 Portal de Técnico & Mesa de Trabajo Dedicada (`/tech`)
- **Experiencia Operativa para el Técnico:** Enrutamiento inteligente por rol (`/tech` vs `/admin`), pestañas dedicadas de "Mis Asignaciones" y "Equipos Disponibles" con auto-asignación en 1 clic (`POST /tickets/{id}/assign-me`).
- **Generación de Acceso a Técnicos:** Provisión de cuentas de acceso con credenciales temporales despachadas automáticamente vía Resend (`POST /technicians/{id}/access`) y gestión en `TechniciansModal`.
- **Modo Supervisor de Solo Lectura:** Acceso de inspección para administradores en `/tech` que preserva la trazabilidad de auditoría deshabilitando mutaciones operativas.
- **Ficha de Reparación Ágil (`TechnicianWorkModal`):** Desbloqueo seguro de PIN/patrón auditado con toggle `Eye`/`EyeOff`, transiciones de estado de 1 clic, vinculación de repuestos y evidencias fotográficas.
- **Ohm (`AiChatBubble` & `AiChatDrawer`):** Burbuja flotante permanente y drawer lateral conversacional potenciado por Gemini 3.6 Flash con modo libre de taller (`POST /diagnostic/chat`) y modo contextualizado al ticket (`POST /tickets/{id}/diagnostic-chat`), botón para volcar diagnósticos y confirmación de aprendizaje RAG.
- **Generación y Edición de Diagnósticos con Ohm:** Creación asistida de diagnósticos técnicos (`POST /tickets/{id}/generate-diagnostic`) con gating de estado (`EN_REPARACION`, `LISTO_PARA_RETIRAR`), borrador editable antes de persistir (`ApplyDiagnosticRequest`) y protección contra regeneración duplicada.
- **Ingreso de Equipos por Técnicos (Delegación Configurable):** Opción opt-in por tienda (`Shop.allow_technician_intake`) administrable desde `SlaSettingsModal` (`PATCH /shops/settings`) que habilita el botón "Ingresar Equipo" en el dashboard técnico (`NewTicketModal`) bajo la guardia `verify_can_create_ticket` con auditoría de creación.

### 🤖 Asistente de Gestión Ohm en Panel de Administrador
- **Copiloto Administrativo para el Taller:** Burbuja flotante y panel deslizable (`AiChatBubble` y `AiChatDrawer`) adaptados con `context="admin"` en `AdminDashboard.jsx` (`POST /admin/assistant/query`).
- **Atajos Rápidos en 1 Clic:** Chips rápidos para métricas clave de negocio: *Ganancias de hoy* (suma de ingresos de tickets listos para entrega), *Equipos ingresados hoy* (conteo diario de recepción) y *Equipos sin tocar* (alerta de equipos estancados por más de 48 horas sin cambio de estado).
- **Catálogo Cerrado de Intents & Cero SQL Injection:** Clasificación estricta mediante coincidencia directa rápida o fallback con `gemini-3.5-flash-lite`, ejecutando consultas SQLAlchemy parametrizadas y emitiendo respuestas enlatadas con ayuda contextual ante consultas fuera del catálogo.
- **Arquitectura Conversacional Stateless:** Operación ágil y ligera en memoria del componente frontend, sin requerir tablas de base de datos ni migraciones de persistencia.

### 🧠 Diagnóstico Asistido con IA (RAG Híbrido & Human-in-the-Loop)
- **Búsqueda Vectorial HNSW:** Recuperación semántica sobre base de conocimiento y casos históricos con `pgvector` (índices HNSW de 768 dimensiones) y aislamiento multi-tenant.
- **Embeddings Locales:** Generación de vectores de texto mediante Ollama (`nomic-embed-text-v2-moe`) con fallback resiliente.
- **Razonamiento Grounded con Gemini 3.6 Flash:** Generación de explicaciones técnicas estructuradas y citaciones verificadas contra alucinaciones.
- **Human-in-the-Loop:** Panel interactivo `DiagnosticAssistPanel` que permite al técnico validar o corregir sugerencias de la IA, retroalimentando la base con casos reales validados (`real_validated`).

### 🌐 Búsqueda Web Técnica (Tavily) & Deep Research en Copiloto Ohm
- **Búsqueda Técnica Especializada:** Integración nativa con la API de Tavily (`search_technical_web`) para consultar en tiempo real diagramas de carga, esquemáticos, pinouts y soluciones comunitarias de reparación.
- **Inyección Contextual de Hallazgos:** Inyección estructurada de fuentes técnicas verificadas directamente en el prompt del modelo de razonamiento (`gemini-3.6-flash`).
- **Trazabilidad y Fuentes Citadas:** Anexado automático del listado de fuentes consultadas con enlaces directos para auditoría técnica por el técnico reparador.
- **Calibración de Recursos:** Presupuesto ampliado a 1500 tokens de salida y timeout específico de 22.0s (`GEMINI_DEEP_RESEARCH_TIMEOUT_SECONDS`), garantizando espacio y tiempo suficientes para razonamiento profundo y emisión de guías paso a paso.

### 🛡️ Gateway LLM Resiliente con Fallback a OmniRoute
- **Desacoplamiento de Proveedores:** Módulo centralizado `llm_gateway.py` para desacoplar las llamadas de IA de los servicios de negocio con soporte multi-tier (`fast` para pre-clasificación/intents y `reasoning` para diagnósticos profundos).
- **Fallback Automático:** Enrutamiento de contingencia hacia proxies compatibles con OpenAI (**OmniRoute**) ante cuotas agotadas (HTTP 429), errores 503 o timeouts de Google Gemini.
- **Detección Preventiva de Truncamiento:** Monitoreo y logging estructurado de advertencia (`llm_max_tokens_reached`) ante respuestas cortadas por tope de tokens (`FinishReason.MAX_TOKENS` / `length`).

### 📦 Inventario y Repuestos
- **Catálogo de Repuestos:** Control de stock, precios de costo y venta, alertas de stock bajo y eliminación lógica.
- **Trazabilidad en Diagnósticos:** Descuento y restauración automática de existencias al vincular o desvincular repuestos a las órdenes de reparación.
- **Validaciones Estrictas:** Reglas de negocio para componentes críticos (ej. displays con marca y modelo obligatorio).

### 🔒 Privacidad, Seguridad y Sanitización de Datos
- **Blindaje de Ohm (Scope Técnico & Anti Prompt-Injection):** Pre-clasificación ligera en una sola llamada JSON con `gemini-3.5-flash-lite` para delimitar consultas estrictamente al dominio de reparación técnica y detectar intentos de jailbreak/inyección. Redirección neutral unificada (`CANNED_REDIRECT_RESPONSE`), técnica sandwich para robustecer el system prompt y registro inmutable de auditoría en `ai_security_events`.
- **Enmascaramiento de PII:** Protección contra *shoulder surfing* en mostrador enmascarando teléfono (`maskPhone`), correo (`maskEmail`) y código de guía (`maskTrackingCode`).
- **Revelado Seguro Bajo Demanda:** Botón interactivo con ícono de ojo (`Eye`/`EyeOff`) en el modal de detalles para técnicos autorizados.
- **Validación Móvil Ecuatoriana:** Validador y normalizador centralizado (`utils/phone.js`) que verifica teléfonos en formato nacional (`09XXXXXXXX`) e internacional (`+5939XXXXXXXX`) para intake y generación fiable de enlaces click-to-chat de WhatsApp.
- **Sanitización Defensiva Multi-Capa:** Validación estricta con Pydantic v2 en backend y guards client-side en formularios (Tickets, Inventario, Técnicos, Login y Registro) que recortan espacios residuales (*trimming*), rechazan entradas puras en blanco y convierten valores vacíos en `null`/`None`.
- **Sanitización de Consultas de Búsqueda:** Filtros de búsqueda en backend (`/tickets`, `/inventory`, `/clients`) con normalización automática de espacios en blanco y coerción a `None` para prevenir falsos negativos con resultados vacíos.
- **Cifrado Simétrico Fernet:** Cifrado en base de datos de contraseñas y patrones de desbloqueo de los dispositivos (`pin_or_password`) con rate limiting y auditoría.
- **Autenticación Robusta:** JWT con tokens de acceso de corta duración, normalización de correos en minúsculas y refresh tokens estatales de un solo uso con rotación y revocación inmediata en logout.
- **Control de Suscripción:** Middleware `subscription_guard` que restringe el acceso con `HTTP 402 Payment Required` ante suscripciones vencidas o suspendidas.

### 🎨 Experiencia Visual y Temas
- **Modo Claro / Modo Oscuro:** Sistema de temas con `ThemeContext` basado en una paleta cálida ámbar calibrada en **OKLCH** y persistencia en `localStorage`.
- **Diseño Atmospheric y N5 Floating Pill:** Barra de navegación flotante y componentes visuales de alto contraste diseñados para entornos de taller.
- **Elevación y Contraste OKLCH en Tarjetas:** Separación visual optimizada de `.ticket-card` y `.tech-ticket-card` mediante `var(--bg-surface)` (delta de luminosidad de +5% en modo oscuro y balance cálido en modo claro) con sombras de elevación estratificadas en ambos temas.
- **Caché Zero-Delay:** Carga instantánea de detalles con React Query (`initialData` y *stale-while-revalidate*).

### 📱 Portal Público de Rastreo & Whitelabeling
- **Acceso por Token Único:** Consulta de estado en tiempo real sin requerir cuenta o login para el cliente.
- **Whitelabeling Dinámico:** Adaptación del portal con el logotipo y nombre comercial del taller.
- **Aprobación de Presupuestos:** El cliente puede autorizar o rechazar presupuestos en línea (con motivo de rechazo opcional).
- **Canal Contextual de WhatsApp:** Botón directo para negociación ágil de presupuestos con el taller.

### 🚀 Landing Page Comercial V2 & Experiencia Interactiva (`/page`)
- **Optimización Mobile P0:** Hero ultra-compacto (<640px) asegurando visibilidad inmediata del headline, la oferta "$0 Primer Mes / 100% Bonificado" y el CTA principal dentro del primer viewport (360x800, 390x844).
- **Navbar Adaptativa <380px:** Ajuste elástico sin desbordes horizontales ni colisiones de controles en pantallas móviles compactas.
- **Workflow Scroll-Driven de 4 Etapas:** Simulación interactiva del flujo del taller con track de 220vh en desktop (`LandingWorkflowDemo`) y avance narrativo (*01 Recibido* → *02 Diagnóstico* → *03 Aprobación* → *04 Listo*), sincronizado con tabs de acceso directo y fallback táctil sin sticky en móviles.
- **Estación de Diagnóstico Ohm (Fidelidad Conversacional):** Stepper interactivo de 4 pasos (*Consulta*, *Memoria del Taller*, *Medición en Multímetro* y *Sugerencia Técnica*) con cita conversacional estructurada de casos históricos reales (#TK-7412) en el diálogo de Ohm, sin métricas porcentuales ficticias, reflejando fielmente la experiencia del chat (`AiChatDrawer`), checklist de 3 puntos, tiempo estimado (~40 min) y panel visual de capitalización en la memoria privada del taller.
- **Estación de Diagnóstico Ohm & Microinteracciones React Bits (Fase 3):** Estación interactiva de 4 etapas (*01 Consulta*, *02 Memoria del Taller*, *03 Mediciones / Hallazgos*, *04 Sugerencia Técnica*) con tres patrones de React Bits adaptados nativamente sin librerías externas (Stepper accesible con navegación por teclado y touch targets $\ge 44\text{px}$, Border Glow continuo de 8s con tokens OKLCH sin neón, y Spotlight Card reactivo al cursor en coordenadas locales desactivado en táctiles), caso factual #TK-7412 (91% de similitud con corto en C3104), multímetro en banco (~450Ω vs 12Ω en corto parcial), checklist de 3 pasos (~40 min), disclaimer de decisión técnica y copy estricto de privacidad y aislamiento multi-tenant en footer.
- **Ambient Tech Dinámico Global:** Atmósfera tecnológica en Canvas (`LandingAmbientTech`) con red de partículas y conexiones vivas por proximidad, modulación reactiva de intensidad por sección y soporte para `prefers-reduced-motion`.
- **Resultados Cualitativos y Programa Piloto:** Secciones estructuradas (`LandingQualitativeResults`, `LandingPilotProgram`, `LandingContactForm`) enfocadas en conversión directa para talleres piloto.
- **Notificación Contextual Sileo:** Toast emergente de conversión (`LandingToastProvider`) con trigger híbrido por intención de salida/scroll y control anti-spam en `sessionStorage` para postulación al Programa Piloto.

---

## Stack Tecnológico

```text
Tecnidesk/
├── backend/     # API REST asíncrona con FastAPI, pgvector y Gemini
└── frontend/    # SPA reactiva con React 19, Vite 7 y Tailwind CSS 4
```

### Backend
- **Lenguaje y Framework:** Python 3.12+, FastAPI
- **Base de Datos & ORM:** PostgreSQL con extensión `pgvector` (HNSW), SQLAlchemy 2.0 (asyncio) y `asyncpg`
- **Control de Migraciones:** Alembic
- **Inteligencia Artificial & RAG:** Google Gemini 3.6 Flash / 3.5 Flash Lite, Ollama (`nomic-embed-text-v2-moe`), `pgvector`
- **Búsqueda Web Técnica & Fallback LLM:** Tavily Search API, OmniRoute (Gateway resiliente compatible con OpenAI)
- **Validación y Configuración:** Pydantic v2, Pydantic Settings
- **Seguridad y Criptografía:** Fernet (`cryptography`), Bcrypt, JWT (`python-jose`)
- **Rate Limiting:** SlowAPI (doble blindaje por user_id)
- **Almacenamiento de Evidencias:** Cloudflare R2 (API S3 compatible)
- **Correo Transaccional:** Resend

### Frontend
- **Framework & Empaquetador:** React 19, Vite 7
- **Enrutamiento:** React Router 7 (con matriz de roles en ProtectedRoute)
- **Estilos & Diseño:** Tailwind CSS 4, Variables CSS (Paleta OKLCH ámbar)
- **Gestión de Estado Asíncrono:** `@tanstack/react-query` v5
- **Iconografía:** `lucide-react`
- **Compresión de Imágenes:** `browser-image-compression` (procesamiento local <800 KB)
- **Testing:** Vitest 3, `@testing-library/react`, `@testing-library/jest-dom`

---

## Estructura del Proyecto

```text
tecnidesk/
├── backend/
│   ├── alembic/              # Migraciones de base de datos
│   ├── app/
│   │   ├── api/v1/           # Endpoints públicos (tracking de tickets)
│   │   ├── core/             # Dependencias, guards de seguridad y rate limiters
│   │   ├── models/           # Modelos ORM (Ticket, Shop, SlaHistory, Diagnostic, etc.)
│   │   ├── routers/          # Controladores (Auth, Tickets, Shops, Technicians, Inventory, etc.)
│   │   ├── schemas/          # Esquemas de validación Pydantic v2
│   │   ├── services/         # Capa de negocio (TicketService, EmbeddingService, etc.)
│   │   ├── config.py         # Configuración centralizada vía Pydantic Settings
│   │   ├── database.py       # Motor asíncrono SQLAlchemy
│   │   └── main.py           # Entrypoint FastAPI, CORS y middleware global
│   ├── scripts/              # Seeds y scripts de sincronización
│   └── tests/                # 243 tests unitarios y de integración con pytest y respx
├── frontend/
│   └── src/
│       ├── api/              # Clientes HTTP (authFetch, tickets, ticketAnalytics, diagnostic, etc.)
│       ├── components/       # Componentes globales y protectores de ruta (ProtectedRoute)
│       ├── context/          # ThemeContext (Modo Claro/Oscuro OKLCH)
│       ├── features/
│       │   ├── admin/        # Módulo administrativo Workbench y asistente Ohm
│       │   ├── analytics/    # Módulo de analítica: tiempos de ciclo y 7 KPIs de negocio
│       │   ├── landing/      # Landing comercial: Workflow 220vh, Ambient Tech y Ohm
│       │   ├── technician/   # Portal de técnico, mesa de trabajo y copiloto Ohm
│       │   └── tracking/     # Portal público de rastreo para clientes
│       ├── pages/            # Login, Registro, AdminAnalyticsPage y Páginas públicas
│       ├── tests/            # 170 tests con Vitest y Testing Library (24 suites)
│       ├── utils/            # Utilidades (PII masking, formateo de fechas y moneda)
│       ├── App.css           # Estilos Workbench y temas OKLCH
│       └── App.jsx           # Rutas y enrutador principal
├── openspec/                 # Especificaciones y cambios archivados bajo SDD
└── PROJECT_STATE.md          # Auditoría técnica e histórico del estado del código
```

---

## Requisitos Previos

- **Python:** 3.12 o superior
- **Node.js:** 18 o superior
- **PostgreSQL:** 14 o superior con extensión `pgvector` instalada
- **Ollama:** Instancia local o remota con modelo `nomic-embed-text-v2-moe` descargado
- **Google Gemini API:** Clave de API con acceso al modelo Gemini 3.6 Flash
- **Cloudflare R2:** Cuenta y credenciales para almacenamiento de evidencias fotográficas
- **Resend:** API Key para envío de correos transaccionales

---

## Instalación y Ejecución Local

### 1. Backend

Desde la raíz del proyecto:

```bash
cd backend
python -m venv .venv

# Activar entorno virtual
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\Activate.ps1 # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
```

Configurar las credenciales en `backend/.env`, aplicar migraciones y ejecutar seed:

```bash
alembic upgrade head
python scripts/seed.py
```

Iniciar el servidor de desarrollo:

```bash
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva disponible en:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

### 2. Frontend

En una terminal independiente:

```bash
cd frontend
npm install

# Configurar URL de la API
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Iniciar servidor de desarrollo
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

---

## Variables de Entorno (Backend)

| Variable | Descripción |
|---|---|
| `DB_URL` | Cadena de conexión asíncrona (`postgresql+asyncpg://...`) |
| `DATABASE_URL` | Cadena de conexión síncrona opcional para CLI y Alembic |
| `JWT_SECRET` | Secreto criptográfico para firma de tokens de acceso (HS256) |
| `JWT_REFRESH_SECRET` | Secreto independiente para refresh tokens estatales |
| `SUPERADMIN_API_KEY` | Clave maestra para activación administrativa de talleres |
| `FERNET_KEY` | Clave Fernet para cifrado simétrico de PINs de dispositivos |
| `BCRYPT_ROUNDS` | Factor de trabajo de hashing para contraseñas (10 en dev, 12 en prod) |
| `GEMINI_API_KEY` | Clave de API de Google Gemini para diagnóstico asistido |
| `GEMINI_PRIMARY_TIMEOUT_SECONDS` | Timeout primario para llamadas a Gemini en segundos (default: `12.0`) |
| `GEMINI_DEEP_RESEARCH_TIMEOUT_SECONDS` | Timeout aislado para flujos de razonamiento técnico con Deep Research (default: `22.0`) |
| `OMNIROUTE_BASE_URL` | URL base para el gateway fallback compatible con OpenAI (ej. `https://api.omniroute.ai/v1`) |
| `OMNIROUTE_API_KEY` | Clave de API para autenticación en el proxy OmniRoute |
| `OMNIROUTE_FAST_COMBO` | Identificador de modelo/combo para tier rápido en OmniRoute (default: `ohm-fast`) |
| `OMNIROUTE_REASONING_COMBO` | Identificador de modelo/combo para tier de razonamiento en OmniRoute |
| `OMNIROUTE_TIMEOUT_SECONDS` | Timeout para llamadas de fallback a OmniRoute en segundos (default: `15.0`) |
| `TAVILY_API_KEY` | Clave de API de Tavily para búsqueda técnica web de esquemáticos y diagramas |
| `TAVILY_TIMEOUT_SECONDS` | Timeout para consultas de búsqueda web en Tavily en segundos (default: `2.5`) |
| `LOCAL_EMBEDDING_SERVICE_URL` | URL de Ollama (`http://localhost:11434`) para embeddings |
| `R2_ENDPOINT` | Endpoint S3 de Cloudflare R2 |
| `R2_ACCESS_KEY` | Access Key de Cloudflare R2 |
| `R2_SECRET_KEY` | Secret Key de Cloudflare R2 |
| `R2_BUCKET_NAME` | Nombre del bucket para evidencias fotográficas |
| `RESEND_API_KEY` | API Key de Resend para correos de recuperación y bienvenida |
| `MAIL_FROM` | Dirección de remitente para correos transaccionales |
| `FRONTEND_URL` | URL base del cliente para construcción de enlaces en correos |
| `ALLOWED_ORIGINS_DEV` | Orígenes locales adicionales permitidos por CORS (separados por coma) |

---

## Pruebas y Calidad de Código

El proyecto cuenta con suites de pruebas automatizadas en backend y frontend con cobertura completa de flujos críticos, lógica multi-tenant, ordenamiento SQL, analíticas y componentes visuales.

### Tests del Backend (Pytest + Respx)

La suite de backend valida modelos, servicios, guards de seguridad, cálculo de tiempos de ciclo y diagnóstico asistido con mocks determinísticos de API:

```bash
cd backend
source .venv/bin/activate

# Ejecutar todos los tests (243 tests pasando al 100%)
pytest

# Ejecutar suite con reporte de cobertura
pytest --cov=app tests/

# Ejecutar directorio específico
pytest tests/integration/
```

### Tests del Frontend (Vitest + Testing Library)

La suite de frontend prueba componentes visuales, interactividad del Workbench Kanban, modales de configuración de SLAs, analíticas de tiempos de ciclo y 7 KPIs ejecutivos, validación móvil ecuatoriana, sanitización client-side y utilidades:

```bash
cd frontend

# Ejecutar todos los tests (170 tests pasando al 100% en 24 suites)
npm test

# Ejecutar con reporte de cobertura
npm run test:coverage
```

---

## Seguridad y Aislamiento

- **Aislamiento Multi-Tenant (Seguridad C1):** Todo endpoint autenticado extrae y valida el `shop_id` desde el token JWT. La capa de servicios reaplica filtros estrictos por tienda en todas las consultas y mutaciones.
- **Blindaje de Ohm (Scope Técnico & Anti Prompt-Injection):** Pre-clasificación en una sola llamada JSON (`gemini-3.5-flash-lite`) que intercepta intentos de jailbreak y temas no técnicos con respuesta neutra enlatada, técnica sandwich en el system prompt y registro inmutable de auditoría en `ai_security_events`.
- **Protección de Datos Sensibles (PII):** Los teléfonos, correos y tokens de clientes se enmascaran visualmente en pantalla por defecto; el PIN de desbloqueo del equipo se almacena cifrado con Fernet y sólo se expone a técnicos autorizados.
- **Sanitización Defensiva de Datos:** Trimming y validación estricta en Pydantic v2 (backend) y formularios reactivos (frontend), impidiendo inyecciones de cadenas vacías o espacios en blanco en campos de texto de clientes, repuestos, técnicos y órdenes.
- **Validación Móvil Ecuatoriana:** Formato estricto (`09XXXXXXXX` / `+5939XXXXXXXX`) para registro de clientes y contacto de talleres, asegurando enlaces de WhatsApp operacionales.
- **Protección contra Fuerza Bruta:** Rate limiting mediante SlowAPI activo en rutas críticas (ej. `/auth/login` limitado a 5 intentos/min por IP).
- **Protección de Transición de Estados:** Guard estricto que impide enviar tickets a reparación sin un técnico responsable asignado.
- **Auditoría Inmutable:** Historial inalterable de cambios de estado registrado en base de datos (`ticket_status_history`).

---

## Despliegue en Producción

| Componente | Plataforma Recomendada | Notas de Despliegue |
|---|---|---|
| **Backend** | Render / Railway / Fly.io | Contenedor ASGI con Python 3.12 |
| **Frontend** | Vercel / Netlify | SPA estática con redirección de rutas (`vercel.json`) |
| **Base de Datos** | Supabase / Neon / AWS RDS | PostgreSQL con extensión `pgvector` activa |
| **Almacenamiento** | Cloudflare R2 | Bucket privado con CORS configurado |
| **Correos** | Resend | Dominio autenticado con DKIM/SPF |

---

## Documentación del Proyecto

El desarrollo y evolución técnica de TecniDesk se gestionan bajo la metodología **Spec-Driven Development (SDD)**:

- [`PROJECT_STATE.md`](PROJECT_STATE.md): Auditoría técnica completa, estado consolidado de la base de código, historial de correcciones y estado del Workbench.
- [`openspec/`](openspec/): Directorio de especificaciones formales del sistema (`openspec/specs/`) y registro cronológico de cambios archivados por ciclo de desarrollo (`openspec/changes/archive/`).

---

## Licencia

Proyecto desarrollado con fines académicos y de titulación. La marca TecniDesk, su identidad visual, arquitectura y datos de cualquier entorno desplegado son propietarios.
