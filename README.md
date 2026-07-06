# TecniDesk 🔧📱

> **Micro SaaS Multi-Tenant** para gestión integral de talleres de reparación de celulares — Diseñado para el mercado ecuatoriano.

TecniDesk cubre todo el ciclo de vida de una reparación: desde el ingreso del equipo hasta la entrega, con un **portal público de rastreo con whitelabeling dinámico** donde el cliente puede consultar el estado, aprobar presupuestos y negociar directamente con el taller vía WhatsApp, todo sin necesidad de crear una cuenta.

---

## ✨ Características Principales

| Área | Funcionalidad |
|---|---|
| 🏢 **Multi-Tenancy** | Cada taller opera en un subdominio único con total aislamiento de datos por `shop_id` |
| 🔐 **Seguridad robusta** | JWT (Access + Refresh), cifrado Fernet para PINs, bcrypt para contraseñas, rate limiting por IP |
| 🎫 **Gestión de Tickets** | Órdenes de reparación completas: diagnóstico, asignación de técnico, estados e ítems de inventario |
| 📸 **Evidencias Fotográficas** | Compresión en el navegador (< 800 KB) antes del upload a Cloudflare R2 |
| 🔍 **Portal de Rastreo Público** | Timeline interactivo del progreso de la reparación, sin login requerido |
| 💬 **Negociación por WhatsApp** | Botón contextual unificado en la etapa de presupuestación para facilitar la conversación con el taller |
| 🎨 **Whitelabeling** | El portal muestra el nombre y logo del taller dinámicamente. TecniDesk aparece solo en el footer como marca secundaria |
| 📊 **Estadísticas en tiempo real** | Conteos reales por estado vía `COUNT() FILTER (WHERE ...)` — nunca truncados por paginación |
| 💰 **Control de Suscripción** | Guard `HTTP 402` que bloquea acceso automáticamente si la suscripción expiró, fue suspendida o cancelada |
| 📧 **Onboarding completo** | Registro captura nombre, subdominio, correo y número de WhatsApp de contacto del taller |

---

## 🏗️ Arquitectura General

```
tecnidesk/
├── backend/     ← API REST (Python / FastAPI)
└── frontend/    ← SPA (React 19 / Vite 7)
```

- El **backend** expone una API REST con documentación interactiva en `/docs` (Swagger UI).
- El **frontend** es una SPA que se comunica exclusivamente con la API, usando JWT para autenticación y `authFetch` para renovar tokens de forma transparente.
- El **multi-tenancy es lógico**: todos los tenants comparten base de datos, aislados por `shop_id` validado en cada operación de la capa de servicios.

---

## 🚀 Stack Tecnológico

### Backend

| Tecnología | Versión | Rol |
|---|---|---|
| **FastAPI** | 0.115 | Framework principal de la API REST |
| **SQLAlchemy** | 2.0 | ORM asíncrono (async/await) |
| **asyncpg** | 0.31 | Driver PostgreSQL de alta performance |
| **Alembic** | 1.14 | Migraciones controladas de base de datos |
| **Pydantic** | v2 | Validación y serialización de esquemas |
| **python-jose** | 3.3 | Generación y verificación de JWT |
| **cryptography (Fernet)** | 43.0 | Cifrado simétrico de PINs de dispositivos |
| **bcrypt / passlib** | 4.0 | Hash seguro de contraseñas de usuarios |
| **SlowAPI** | 0.1.9 | Rate limiting por IP en rutas vulnerables |
| **aioboto3** | 13.2 | Integración con Cloudflare R2 (evidencias) |
| **resend** | 2.23 | Correos transaccionales |
| **uvicorn** | 0.30 | Servidor ASGI |

### Frontend

| Tecnología | Versión | Rol |
|---|---|---|
| **React** | 19 | Biblioteca UI principal |
| **Vite** | 7 | Build tool y servidor de desarrollo ultra-rápido |
| **TypeScript** | 5.9 | Tipado progresivo (JS + TS) |
| **React Router** | v7 | Enrutado client-side con guards de protección |
| **Tailwind CSS** | v4 | Estilos utility-first, integrado nativamente en Vite |
| **browser-image-compression** | 2.0 | Compresión de imágenes antes del upload |

---

## 🗄️ Modelos de Base de Datos

```
plans             → Planes de suscripción disponibles
shops             → Tenants (talleres): subdominio único, logo, estado de suscripción, WhatsApp
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

1. **Aislamiento Multi-Tenant** — Cada query filtra por `shop_id` del usuario en sesión. Un taller nunca puede acceder a datos de otro.
2. **Subscription Guard** — Middleware de ruta que consulta la tabla `subscriptions`. Retorna `HTTP 402` si la suscripción es inválida.
3. **Cifrado Fernet** — El PIN del dispositivo se cifra antes de persistirse. Solo se desencripta en la capa de servicios interna.
4. **JWT de doble capa** — Access tokens de 60 min + Refresh tokens stateful de 7 días con Single-Use Rotation para prevenir replay attacks.
5. **CORS con Regex** — Solo acepta orígenes de producción que sean subdominios del dominio principal configurado.
6. **Rate Limiting** — `5 req/min` en `/auth/login` y `30 req/min` en el endpoint de tracking público, por IP.

---

## 📁 Estructura de Directorios

<details>
<summary><strong>Backend — <code>backend/</code></strong></summary>

```
backend/
├── app/
│   ├── api/v1/endpoints/
│   │   └── tracking.py        ← Endpoint público de rastreo (sin auth)
│   ├── core/
│   │   └── dependencies.py    ← get_current_user, subscription_guard
│   ├── models/                ← Modelos ORM SQLAlchemy 2.0
│   ├── routers/               ← Controladores REST (auth, tickets, shops, health)
│   ├── schemas/               ← Esquemas Pydantic v2 de entrada/salida
│   ├── services/              ← Lógica de negocio (auth, tickets, email, storage)
│   ├── config.py              ← Variables de entorno con Pydantic Settings
│   ├── database.py            ← Motor de conexión asíncrono
│   └── main.py                ← Entry point (FastAPI, CORS, middlewares)
├── alembic/                   ← Control de migraciones de la base de datos
├── scripts/
│   ├── seed.py                ← Datos iniciales (planes de suscripción)
│   └── activate_shop.py       ← Activación manual de tiendas vía CLI
├── .env.example
├── requirements.txt
└── alembic.ini
```

</details>

<details>
<summary><strong>Frontend — <code>frontend/</code></strong></summary>

```
frontend/
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
│   │   └── TrackingPortal.jsx ← Portal público con whitelabeling dinámico
│   ├── utils/                 ← Constantes de estado, formateo de fechas y utilidades
│   ├── App.jsx                ← Definición de rutas con React Router
│   └── main.tsx               ← Entry point React
├── public/
├── vercel.json                ← SPA routing para Vercel
├── index.html
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
- **Cloudflare R2** — Almacenamiento de evidencias fotográficas
- **Resend** — Correos transaccionales

---

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/tecnidesk.git
cd tecnidesk
```

---

### 2. Configurar el Backend

```bash
cd backend

# Crear y activar entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Variables de Entorno

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
| `JWT_SECRET` | Cadena aleatoria ≥ 64 chars |
| `JWT_REFRESH_SECRET` | Segunda cadena aleatoria ≥ 64 chars (distinta a la anterior) |
| `FERNET_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `BCRYPT_ROUNDS` | Factor de trabajo bcrypt (`10` dev / `12` prod) |
| `R2_ENDPOINT` | URL del bucket Cloudflare R2 |
| `R2_ACCESS_KEY` | Access Key de Cloudflare R2 |
| `R2_SECRET_KEY` | Secret Key de Cloudflare R2 |
| `R2_BUCKET_NAME` | Nombre del bucket (ej: `tecnidesk-evidencias`) |
| `RESEND_API_KEY` | API Key de Resend |
| `WEBHOOK_URL` | Endpoint externo para notificaciones de cambio de estado |
| `WEBHOOK_SECRET` | Secreto HMAC para validar autenticidad de webhooks |
| `ALLOWED_ORIGINS_DEV` | Orígenes CORS locales (ej: `http://localhost:5173`) |

#### Migraciones y datos iniciales

```bash
alembic upgrade head
python scripts/seed.py
```

#### Iniciar servidor

```bash
uvicorn app.main:app --reload --port 8000
```

> Documentación interactiva disponible en `http://localhost:8000/docs`

---

### 3. Configurar el Frontend

```bash
cd frontend
npm install
```

Crea el archivo `.env.local` con la URL de tu API:

```env
VITE_API_URL=http://localhost:8000
```

#### Iniciar servidor

```bash
npm run dev
```

> La aplicación estará disponible en `http://localhost:5173`

---

## 🖥️ Flujos Principales

### Panel Administrativo (`/admin`)
- Dashboard con estadísticas en tiempo real por estado, obtenidas del endpoint dedicado `GET /tickets/stats`
- Creación de tickets con carga de evidencia fotográfica inicial en el mismo flujo
- Cambio de estado con actualizaciones optimistas en la UI
- Asignación de técnicos y actualización de diagnósticos
- PIN del dispositivo visible y desencriptado tras cada actualización (nunca almacenado en texto plano)

### Portal de Rastreo Público (`/tracking/:token`)
- Acceso sin login mediante token único por ticket
- Timeline interactivo (Stepper) con el progreso de la reparación
- Aprobación o rechazo de presupuestos directamente desde el portal
- Botón WhatsApp contextualizado en la etapa de presupuestación con microcopy orientado a la negociación
- Whitelabeling dinámico: nombre y logo del taller desde el backend — "Impulsado por TecniDesk" solo en el footer

---

## 🚢 Despliegue en Producción

| Servicio | Plataforma Recomendada |
|---|---|
| **Backend** | [Render](https://render.com) (Web Service Python) o VPS con Docker |
| **Frontend** | [Vercel](https://vercel.com) — `vercel.json` ya configurado para SPA routing |
| **Base de Datos** | [Supabase](https://supabase.com) (PostgreSQL administrado) |
| **Almacenamiento** | [Cloudflare R2](https://www.cloudflare.com/products/r2/) |
| **Email** | [Resend](https://resend.com) |

---

## 🗺️ Roadmap y Deuda Técnica

### Pendientes Críticos

- [ ] **FASE 4 — Vulnerabilidad IDOR en activación de tiendas:** El endpoint `/admin/activate-shop` solo verifica un usuario autenticado genérico. Debe protegerse con un `admin_guard` de super-administrador global. Activación disponible por ahora vía CLI (`scripts/activate_shop.py`).
- [ ] **Blacklist de JWT con Redis:** Los Access Tokens (60 min) sobreviven al logout manual. Pendiente implementar invalidación inmediata con TTL en Redis.

### Mejoras Planificadas

- [ ] **Worker de tareas asíncronas (ARQ / Celery + Redis):** Garantizar durabilidad en reintentos de webhooks ante reinicios del proceso.
- [ ] **URLs prefirmadas para evidencias (R2):** Reemplazar buckets públicos por Pre-signed URLs de corta duración.
- [ ] **TanStack Query en el frontend:** Migrar de `useState` / `useEffect` a caché automatizada con stale-while-revalidate.
- [ ] **RBAC estructurado:** Roles y permisos granulares: super-admin SaaS, admin de taller, técnico.

---

## 📋 Historial de Correcciones

| Fase | Descripción |
|---|---|
| **FASE 1 (BUG-02)** | Pérdida de datos del cliente al cambiar estados → `selectinload` en SQLAlchemy + preservación de estado local en React |
| **FASE 2 (BUG-01)** | Desaparición del PIN y correo al crear tickets → endpoint POST retorna esquema anidado completo `TicketListResponse` |
| **FASE 3 (BUG-03)** | Subida de evidencia desde modal de creación → pipeline secuencial con `FormData` nativo |
| **FASE 5** | Estadísticas reales del dashboard → endpoint `GET /tickets/stats` con `COUNT() FILTER` en PostgreSQL |
| **Fix PIN** | Parpadeo "Sin PIN" tras actualización → `update_ticket_status`, `update_ticket_diagnostic` y `assign_technician` desencriptan antes de retornar |
| **Whitelabeling** | Portal de rastreo con nombre y logo dinámico del taller → `shop_name` + `shop_logo_url` en `PublicTicketResponse`; columna `logo_url` en tabla `shops` |
| **WhatsApp** | Botón de WhatsApp ausente en registros antiguos → `contact_whatsapp` capturado en onboarding; backend retorna `None` en vez de string vacío |

---

## 🎨 Guía de Estilo (Frontend)

Paleta oscura premium optimizada para visibilidad en talleres técnicos:

- **Accent (Dorado):** `#C9A76A` — Botones primarios e indicadores destacados
- **Success (Verde WhatsApp):** `#25D366` — Canal de comunicación y estados exitosos
- **Background:** Modo oscuro profundo con capas de glassmorphism
- **Tipografía:** Jerarquía clara con fuentes del sistema modernas

---

## 📄 Licencia

Proyecto desarrollado como parte de un proyecto de titulación académica. Todos los derechos reservados.

---

<p align="center">
  Construido con ❤️ para talleres de celulares en Ecuador<br/>
  <strong>TecniDesk</strong> — Gestión técnica, sin complicaciones.
</p>
