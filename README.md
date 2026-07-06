# TecniDesk 🔧📱

> **Micro SaaS Multi-Tenant** para gestión integral de talleres de reparación de celulares — Diseñado para el mercado ecuatoriano.

TecniDesk es una solución web moderna con arquitectura desacoplada que cubre todo el ciclo de vida de una reparación: desde el ingreso del equipo hasta la entrega al cliente, con un **portal público de rastreo con whitelabeling dinámico** donde el cliente puede aprobar o rechazar presupuestos en tiempo real y negociar directamente con el taller vía WhatsApp.

---

## ✨ Características Principales

| Área | Funcionalidad |
|---|---|
| 🏢 **Multi-Tenancy** | Cada taller opera en un subdominio único con total aislamiento de datos por `shop_id` |
| 🔐 **Seguridad robusta** | JWT (Access/Refresh), cifrado Fernet para PINs de dispositivos, bcrypt para contraseñas, rate limiting |
| 🎫 **Gestión de Tickets** | Órdenes de reparación completas: diagnóstico, asignación de técnico, estados e ítems de inventario |
| 📸 **Evidencias Fotográficas** | Subida de fotos del estado del equipo con compresión en el navegador (< 800 KB) antes del envío |
| 🔍 **Portal de Rastreo Público** | Acceso sin login mediante token único, con timeline interactivo del progreso de la reparación |
| 💬 **Negociación por WhatsApp** | Botón contextual unificado en la etapa de presupuestación que conecta directamente al cliente con el taller para facilitar la negociación |
| 🎨 **Whitelabeling** | El portal de rastreo muestra el nombre y logo del taller dinámicamente. TecniDesk actúa como marca secundaria ("Impulsado por TecniDesk") |
| 📊 **Estadísticas en tiempo real** | Dashboard con conteos reales de tickets por estado mediante `COUNT() FILTER (WHERE ...)` en PostgreSQL — nunca truncados por paginación |
| 💰 **Control de Suscripción** | Guard HTTP 402 que bloquea el acceso automáticamente si la suscripción del taller expiró, fue suspendida o cancelada |
| 📧 **Onboarding completo** | Registro de talleres capturando nombre, subdominio, correo y número de WhatsApp de contacto |

---

## 🏗️ Arquitectura General

```
TECNIDESK/
├── Tecnidesk-backend/    ← API REST (Python / FastAPI)
└── Tecnidesk-frontend/   ← SPA (React 19 / Vite 7)
```

El sistema implementa una **arquitectura cliente-servidor desacoplada**:

- El **backend** expone una API REST documentada automáticamente en `/docs` (Swagger UI).
- El **frontend** es una SPA que se comunica exclusivamente a través de la API, usando JWT para autenticación y un helper `authFetch` para renovar tokens transparentemente.
- El **multi-tenancy** es lógico: todos los tenants comparten la misma base de datos, aislados mediante `shop_id` validado en cada operación de la capa de servicios.

---

## 🚀 Stack Tecnológico

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| **FastAPI** | 0.115 | Framework principal de la API REST |
| **SQLAlchemy** | 2.0 | ORM asíncrono (patrones async/await) |
| **asyncpg** | 0.31 | Driver PostgreSQL de alta performance |
| **Alembic** | 1.14 | Migraciones controladas de base de datos |
| **Pydantic** | v2 | Validación y serialización de esquemas |
| **python-jose** | 3.3 | Generación y verificación de JWT |
| **cryptography (Fernet)** | 43.0 | Cifrado simétrico de PINs de dispositivos |
| **bcrypt / passlib** | 4.0 | Hash seguro de contraseñas de usuarios |
| **SlowAPI** | 0.1.9 | Rate limiting por IP en rutas vulnerables |
| **aioboto3 / boto3** | 13.2 | Integración con Cloudflare R2 (almacenamiento de evidencias) |
| **resend** | 2.23 | Envío de correos transaccionales |
| **uvicorn** | 0.30 | Servidor ASGI de producción |

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| **React** | 19 | Biblioteca UI principal |
| **Vite** | 7 | Build tool y servidor de desarrollo ultra-rápido |
| **TypeScript** | 5.9 | Tipado progresivo (JS + TS) |
| **React Router** | v7 | Enrutado client-side con guards de protección |
| **Tailwind CSS** | v4 | Estilos utility-first, integrado nativamente en Vite |
| **browser-image-compression** | 2.0 | Compresión de imágenes en el cliente antes del upload |

---

## 🗄️ Modelos de Base de Datos

```
plans             → Planes de suscripción disponibles
shops             → Tenants (talleres), con subdominio único, logo y estado de suscripción
subscriptions     → Fuente de verdad del estado de pago por taller
users             → Personal del taller (admin / technician)
refresh_tokens    → Tokens de refresco stateful con hash SHA-256 (rotación de un solo uso)
customers         → Clientes del taller (índice compuesto shop_id + phone_number)
inventory         → Catálogo de repuestos y mano de obra con alertas de stock bajo
tickets           → Órdenes de reparación (tracking_token auto-generado, PIN cifrado con Fernet)
ticket_items      → Repuestos e insumos vinculados a un ticket
ticket_evidences  → Fotos y archivos de evidencia subidos a Cloudflare R2
webhook_logs      → Historial de llamadas a webhooks externos por cambio de estado
```

---

## 🔒 Mecanismos de Seguridad

1. **Aislamiento Multi-Tenant:** Cada query en la capa de servicios filtra por el `shop_id` del usuario en sesión. Es imposible que un taller acceda a datos de otro.
2. **Subscription Guard:** Middleware de ruta que consulta directamente la tabla `subscriptions`. Devuelve `HTTP 402` si la suscripción es inválida.
3. **Cifrado Fernet:** El PIN o patrón de desbloqueo del celular se cifra simétricamente antes de persistirse y solo se desencripta en la capa de servicios interna.
4. **JWT de doble capa:** Access tokens de 60 min + Refresh tokens stateful de 7 días con rotación de un solo uso (Single-Use Rotation) para prevenir ataques de replay.
5. **CORS con Regex:** Valida que los orígenes de producción sean únicamente subdominios del dominio principal configurado.
6. **Rate Limiting:** `5 req/min` en `/auth/login` y `30 req/min` en el endpoint de tracking público, ambos filtrados por IP.

---

## 📁 Estructura de Directorios

<details>
<summary><strong>Backend — <code>Tecnidesk-backend/</code></strong></summary>

```
Tecnidesk-backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── tracking.py        ← Endpoint público de rastreo (sin auth requerida)
│   ├── core/
│   │   └── dependencies.py    ← get_current_user, subscription_guard
│   ├── models/                ← Modelos ORM SQLAlchemy 2.0
│   ├── routers/               ← Controladores REST (auth, tickets, shops, health)
│   ├── schemas/               ← Esquemas Pydantic v2 de entrada/salida
│   ├── services/              ← Lógica de negocio (auth, tickets, email, storage)
│   ├── config.py              ← Variables de entorno con Pydantic Settings
│   ├── database.py            ← Motor de conexión asíncrono
│   └── main.py                ← Entrada principal (FastAPI, CORS, middlewares)
├── alembic/                   ← Control de migraciones de la base de datos
├── scripts/
│   ├── seed.py                ← Poblar datos iniciales (planes, etc.)
│   └── activate_shop.py       ← Activación manual de tiendas vía CLI
├── requirements.txt
└── alembic.ini
```

</details>

<details>
<summary><strong>Frontend — <code>Tecnidesk-frontend/</code></strong></summary>

```
Tecnidesk-frontend/
├── src/
│   ├── api/                   ← Base URL y authFetch (interceptor JWT automático)
│   ├── components/
│   │   ├── guards/            ← ProtectedRoute y PublicRoute
│   │   └── shared/            ← LogoBadge, Skeleton, Stepper y componentes comunes
│   ├── features/admin/
│   │   ├── components/        ← AdminTicketCard, NewTicketModal y demás modales
│   │   └── AdminDashboard.jsx ← Panel administrativo principal
│   ├── pages/
│   │   ├── HomePage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   └── TrackingPortal.jsx ← Portal público de rastreo con whitelabeling dinámico
│   ├── utils/                 ← Constantes de estado, formateo de fechas y utilidades
│   ├── App.jsx                ← Definición de rutas con React Router
│   └── main.tsx               ← Entry point React
├── public/
├── vercel.json                ← Configuración de SPA routing para Vercel
├── package.json
└── vite.config.ts
```

</details>

---

## ⚙️ Instalación y Configuración

### Prerrequisitos

- **Python** 3.12+
- **Node.js** 18+
- **PostgreSQL** 14+ (o cuenta en [Supabase](https://supabase.com))
- **Cloudflare R2** — Para almacenamiento de evidencias fotográficas
- **Resend** — Para correos transaccionales (restablecimiento de contraseña, notificaciones)

---

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/tecnidesk.git
cd tecnidesk
```

---

### 2. Configurar el Backend

```bash
cd Tecnidesk-backend

# Crear entorno virtual
python -m venv .venv

# Activar en Windows
.venv\Scripts\activate
# Activar en Linux / macOS
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Variables de Entorno

Copia el archivo de ejemplo y rellena los valores:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

| Variable | Descripción |
|---|---|
| `DB_URL` | Conexión asíncrona: `postgresql+asyncpg://user:pass@host:port/db` |
| `DATABASE_URL` | Conexión síncrona para Alembic CLI: `postgresql://user:pass@host:port/db` |
| `JWT_SECRET` | Cadena aleatoria ≥ 64 chars — `openssl rand -hex 32` |
| `JWT_REFRESH_SECRET` | Segunda cadena aleatoria ≥ 64 chars (diferente a la anterior) |
| `FERNET_KEY` | Clave Fernet: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `BCRYPT_ROUNDS` | Factor de trabajo bcrypt (recomendado: `10` en dev, `12` en prod) |
| `R2_ENDPOINT` | URL del bucket de Cloudflare R2 |
| `R2_ACCESS_KEY` | Access Key de Cloudflare R2 |
| `R2_SECRET_KEY` | Secret Key de Cloudflare R2 |
| `R2_BUCKET_NAME` | Nombre del bucket (ej: `tecnidesk-evidencias`) |
| `RESEND_API_KEY` | API Key de Resend para correos transaccionales |
| `WEBHOOK_URL` | Endpoint externo para notificaciones de cambio de estado |
| `WEBHOOK_SECRET` | Secreto HMAC para validar la autenticidad de los webhooks |
| `ALLOWED_ORIGINS_DEV` | Orígenes CORS para dev local (ej: `http://localhost:5173`) |

#### Migraciones y Seed

```bash
# Aplicar migraciones al esquema de la base de datos
alembic upgrade head

# Poblar datos iniciales (planes de suscripción)
python scripts/seed.py
```

#### Iniciar servidor de desarrollo

```bash
uvicorn app.main:app --reload --port 8000
```

> La documentación interactiva estará disponible en `http://localhost:8000/docs`.

---

### 3. Configurar el Frontend

```bash
cd Tecnidesk-frontend

# Instalar dependencias
npm install
```

Crea el archivo `.env.local` en la raíz del frontend con la URL de tu API:

```env
VITE_API_URL=http://localhost:8000
```

#### Iniciar servidor de desarrollo

```bash
npm run dev
```

> La aplicación estará disponible en `http://localhost:5173`.

---

## 🖥️ Flujos Principales

### Panel Administrativo (`/admin`)
- Dashboard con estadísticas en tiempo real (total de equipos, en reparación, listos para entrega) mediante endpoint dedicado `/tickets/stats`
- Creación de tickets con carga de evidencia fotográfica inicial en el mismo flujo
- Cambio de estado del equipo con actualizaciones optimistas en la UI
- Asignación de técnicos y actualización de diagnósticos
- El PIN del dispositivo se muestra desencriptado al técnico asignado tras cada actualización (nunca se almacena en texto plano)

### Portal de Rastreo Público (`/tracking/:token`)
- Acceso sin login mediante token único generado por ticket
- Timeline interactivo (Stepper) con el progreso de la reparación
- Aprobación o rechazo de presupuestos directamente desde el portal
- **Canal de negociación WhatsApp:** Botón contextual unificado en la etapa de presupuestación con microcopy optimizado para facilitar la conversación con el taller
- **Whitelabeling dinámico:** Muestra el nombre y logo del taller obtenidos del backend — TecniDesk aparece solo como "Impulsado por TecniDesk" en el footer

---

## 🚢 Despliegue en Producción

| Servicio | Plataforma Recomendada |
|---|---|
| **Backend** | [Render](https://render.com) (Web Service, Python) o VPS con Docker |
| **Frontend** | [Vercel](https://vercel.com) — incluye `vercel.json` configurado para SPA routing |
| **Base de Datos** | [Supabase](https://supabase.com) (PostgreSQL administrado) |
| **Almacenamiento de Evidencias** | [Cloudflare R2](https://www.cloudflare.com/products/r2/) |
| **Email Transaccional** | [Resend](https://resend.com) |

---

## 🗺️ Roadmap y Deuda Técnica

### Pendientes Críticos

- [ ] **Vulnerabilidad IDOR en activación de tiendas (FASE 4):** El endpoint `/admin/activate-shop` solo verifica un usuario autenticado genérico. Debe protegerse con un `admin_guard` de super-administrador global que aún no existe. La activación se realiza por ahora vía CLI (`scripts/activate_shop.py`).
- [ ] **Blacklist de JWT con Redis:** Los Access Tokens (60 min) sobreviven al logout manual. Pendiente implementar invalidación inmediata con TTL en Redis.

### Mejoras Planificadas

- [ ] **Worker de tareas asíncronas (ARQ/Celery + Redis):** Reemplazar `BackgroundTasks` + `asyncio.sleep` para garantizar durabilidad en reintentos de webhooks ante reinicios del proceso.
- [ ] **URLs prefirmadas para evidencias (R2):** Actualmente los buckets son públicos. Generar Pre-signed URLs de vida corta para mejorar la privacidad de las evidencias fotográficas.
- [ ] **TanStack Query en el frontend:** Migrar el manejo de estado de red de `useState`/`useEffect` a caché automatizada con stale-while-revalidate.
- [ ] **RBAC estructurado:** Implementar roles y permisos granulares a nivel de plataforma SaaS (super-admin, admin de taller, técnico).

---

## 📋 Historial de Correcciones (Changelog)

| Sesión | Cambio |
|---|---|
| **FASE 1 (BUG-02)** | Resuelto: pérdida de datos del cliente al cambiar estados en el panel — `selectinload` en SQLAlchemy + preservación de estado local en React |
| **FASE 2 (BUG-01)** | Resuelto: desaparición del PIN y correo al crear tickets — endpoint POST devuelve esquema anidado completo `TicketListResponse` |
| **FASE 3 (BUG-03)** | Resuelto: subida de evidencia fotográfica inicial desde el modal de creación — pipeline secuencial con `FormData` nativo |
| **FASE 5** | Resuelto: estadísticas reales del dashboard — endpoint dedicado `GET /tickets/stats` con `COUNT() FILTER` en PostgreSQL, eliminando dependencia de `tickets.length` |
| **Fix PIN** | Resuelto: parpadeo "Sin PIN" tras actualización de ticket — las funciones `update_ticket_status`, `update_ticket_diagnostic` y `assign_technician` ahora desencriptan el PIN antes de retornar |
| **Whitelabeling** | Resuelto: portal de rastreo muestra nombre y logo dinámico del taller — `shop_name` y `shop_logo_url` en `PublicTicketResponse`; columna `logo_url` en tabla `shops` |
| **WhatsApp** | Resuelto: botón de WhatsApp no aparecía en portales con registros antiguos — `contact_whatsapp` ahora se captura en el onboarding (`RegisterRequest`) y el endpoint de tracking devuelve `None` en vez de string vacío |

---

## 🎨 Guía de Estilo (Frontend)

El sistema utiliza una paleta oscura premium optimizada para visibilidad en talleres técnicos:

- **Accent (Dorado):** `#C9A76A` — Botones primarios e indicadores destacados
- **Success (Verde WhatsApp):** `#25D366` — Canal de comunicación y estados exitosos
- **Background:** Modo oscuro profundo con capas de glassmorphism
- **Tipografía:** Jerarquía tipográfica clara con fuentes del sistema modernas

---

## 📄 Licencia

Este proyecto fue desarrollado como parte de un proyecto de titulación académica. Todos los derechos reservados.

---

<p align="center">
  Construido con ❤️ para talleres de celulares en Ecuador<br/>
  <strong>TecniDesk</strong> — Gestión técnica, sin complicaciones.
</p>
