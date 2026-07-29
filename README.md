# TecniDesk

Micro SaaS multi-tenant para la gestión de talleres de reparación de celulares.

TecniDesk centraliza el ingreso de equipos, clientes, tickets de reparación, diagnósticos, repuestos, evidencias fotográficas, presupuestos y seguimiento público. Cada taller trabaja aislado mediante su `shop_id` y puede ofrecer a sus clientes un portal de rastreo con identidad visual propia.

## Funcionalidades

- Panel administrativo para gestionar tickets, clientes, técnicos y estados de reparación.
- Gestión de Técnicos con métricas de rendimiento, especialidades inferidas y asignación automática (Load-Balancing).
- Inventario de repuestos con altas, edición, eliminación lógica, reabastecimiento y alertas de stock bajo.
- Sugerencias de repuestos frecuentes y selección de piezas desde el inventario al preparar un diagnóstico.
- Diagnóstico técnico con repuestos, cantidades y precios asociados al ticket.
- Descuento y restauración de stock al agregar o quitar piezas de una reparación.
- Evidencias fotográficas comprimidas en el navegador antes de enviarse al almacenamiento.
- Portal público de seguimiento mediante token, sin cuenta para el cliente.
- Aprobación o rechazo de presupuestos desde el portal de seguimiento.
- Contacto contextual con el taller mediante WhatsApp.
- Whitelabeling: nombre y logotipo del taller en el portal público.
- Autenticación con JWT de acceso y refresh tokens persistentes.
- Control de suscripción mediante `HTTP 402` cuando el plan no está vigente.
- Estadísticas del panel calculadas directamente en PostgreSQL.

## Arquitectura

```text
Tecnidesk/
├── backend/     API REST con FastAPI
└── frontend/    SPA con React y Vite
```

El backend expone la API y concentra la autenticación, autorización, aislamiento multi-tenant, lógica de negocio, persistencia y migraciones. El frontend consume la API mediante `authFetch`, que adjunta el token de acceso y gestiona la renovación de sesión.

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 con consultas asíncronas
- PostgreSQL y `asyncpg`
- Alembic
- Pydantic v2
- JWT, Fernet y bcrypt
- SlowAPI para rate limiting
- Cloudflare R2 para evidencias
- Resend para correos transaccionales

### Frontend

- React 19
- Vite 7
- React Router 7
- Tailwind CSS 4 y variables CSS del proyecto
- `lucide-react` para iconografía
- `browser-image-compression` para evidencias fotográficas

## Estructura principal

```text
backend/
├── app/
│   ├── api/v1/       Endpoints públicos de tracking
│   ├── core/         Dependencias, guards y rate limiting
│   ├── models/       Modelos SQLAlchemy
│   ├── routers/      Rutas FastAPI
│   ├── schemas/      Esquemas Pydantic
│   ├── services/     Lógica de negocio
│   ├── config.py     Configuración desde variables de entorno
│   ├── database.py   Conexión asíncrona a PostgreSQL
│   └── main.py       Aplicación FastAPI, CORS y middlewares
├── alembic/          Migraciones de base de datos
├── scripts/          Seeds y tareas operativas
├── requirements.txt
└── alembic.ini

frontend/
├── src/
│   ├── api/                      Cliente HTTP y configuración de API
│   ├── components/               Componentes compartidos y guards
│   ├── features/admin/           Dashboard y componentes administrativos
│   ├── pages/                    Login, registro y tracking público
│   ├── utils/                    Estados y utilidades
│   ├── App.jsx
│   └── main.tsx
├── public/
├── package.json
├── vercel.json
└── vite.config.ts
```

## Requisitos

- Python 3.12 o superior
- Node.js 18 o superior
- PostgreSQL 14 o superior, local o administrado
- Credenciales de Cloudflare R2 para evidencias
- API key de Resend para correos transaccionales

## Instalación local

### Backend

Desde la raíz del proyecto:

```bash
cd backend
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux o macOS
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Crear la configuración local:

```bash
# Windows
Copy-Item .env.example .env

# Linux o macOS
cp .env.example .env
```

Aplicar migraciones y cargar datos iniciales:

```bash
alembic upgrade head
python scripts/seed.py
```

Iniciar la API:

```bash
uvicorn app.main:app --reload --port 8000
```

Documentación interactiva:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

### Frontend

En otra terminal:

```bash
cd frontend
npm install
```

Crear `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

Iniciar el servidor de desarrollo:

```bash
npm run dev
```

La aplicación estará disponible normalmente en `http://localhost:5173`.

## Variables de entorno

Las variables del backend se configuran en `backend/.env`. No deben subirse al repositorio.

| Variable | Uso |
|---|---|
| `DB_URL` | Conexión asíncrona de la aplicación, normalmente con `postgresql+asyncpg://` |
| `DATABASE_URL` | Conexión síncrona opcional para herramientas CLI |
| `JWT_SECRET` | Secreto para tokens de acceso |
| `JWT_REFRESH_SECRET` | Secreto independiente para refresh tokens |
| `FERNET_KEY` | Clave para cifrar datos sensibles del dispositivo |
| `BCRYPT_ROUNDS` | Factor de trabajo para contraseñas |
| `R2_ENDPOINT` | Endpoint de Cloudflare R2 |
| `R2_ACCESS_KEY` | Credencial de acceso a R2 |
| `R2_SECRET_KEY` | Credencial secreta de R2 |
| `R2_BUCKET_NAME` | Bucket para evidencias |
| `RESEND_API_KEY` | API key para correo transaccional |
| `MAIL_FROM` | Remitente de correos |
| `WEBHOOK_URL` | Endpoint opcional de notificaciones |
| `WEBHOOK_SECRET` | Secreto para validar webhooks |
| `FRONTEND_URL` | URL pública usada en enlaces enviados por correo |
| `ALLOWED_ORIGINS_DEV` | Orígenes locales permitidos por CORS, separados por comas |

En el frontend, `VITE_API_URL` debe apuntar al backend correspondiente al entorno. En producción no debe conservar la URL local `http://localhost:8000`.

## Flujo operativo

1. El administrador registra un cliente y crea un ticket con los datos del equipo.
2. El taller actualiza el estado, asigna técnico y registra evidencias.
3. El técnico documenta el diagnóstico y agrega mano de obra o repuestos.
4. Las piezas vinculadas al inventario descuentan stock de forma controlada.
5. El cliente recibe o consulta el enlace público de seguimiento.
6. El cliente aprueba, rechaza o negocia el presupuesto desde el portal.
7. El taller continúa el flujo hasta marcar la reparación como lista para entregar.

## Inventario

El módulo de inventario está disponible desde el panel administrativo y soporta:

- Nombre, costo, precio de venta y stock inicial.
- Umbral configurable de stock bajo.
- Validación de cantidades enteras y valores monetarios no negativos.
- Sugerencias de repuestos comunes, como pines de carga, baterías, displays y flex.
- Regla de negocio para displays: deben registrarse con marca y modelo.
- Reabastecimiento y eliminación lógica para conservar el historial de tickets.

El endpoint utiliza el aislamiento del taller autenticado. Un usuario sólo puede consultar o modificar inventario asociado a su propio `shop_id`.

## Despliegue

La distribución recomendada es:

| Componente | Plataforma |
|---|---|
| Backend | Render u otro servicio ASGI |
| Frontend | Vercel |
| Base de datos | PostgreSQL administrado, por ejemplo Supabase |
| Archivos | Cloudflare R2 |
| Correo | Resend |

Antes de desplegar:

1. Confirmar que las migraciones están incluidas en el commit publicado.
2. Ejecutar `alembic upgrade head` contra la base de datos de producción.
3. Configurar `VITE_API_URL` en el proyecto del frontend.
4. Configurar `FRONTEND_URL` y los orígenes permitidos en el backend.
5. Revisar los logs del backend después de cada migración o cambio de variables.
6. Verificar el flujo de login, creación de ticket, inventario y tracking público.

## Comandos útiles

```bash
# Backend
cd backend
alembic current
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
npm run build
npm run lint
```

## Seguridad

- El aislamiento multi-tenant se aplica mediante el `shop_id` del usuario autenticado. Las dependencias resuelven la identidad y la suscripción del taller, y la capa de servicios vuelve a filtrar las consultas y mutaciones por ese identificador.
- Las contraseñas se almacenan con hash bcrypt.
- Los PIN o datos sensibles del dispositivo se cifran con Fernet.
- Los refresh tokens se almacenan de forma persistente y se rotan.
- Las rutas sensibles utilizan guards de autenticación y suscripción.
- El acceso público al tracking se limita al token del ticket.
- CORS debe configurarse con los dominios reales de cada entorno.
- Los secretos deben permanecer únicamente en las variables de entorno del despliegue.

### Rate limiting

SlowAPI limita `POST /auth/login` a `5 intentos por minuto y por IP`. Esto reduce intentos automatizados de fuerza bruta sobre las credenciales. El portal público de tracking utiliza tokens de ticket y no requiere sesión; cualquier límite adicional para esos endpoints debe considerarse una mejora independiente y no se presenta aquí como una protección ya implementada.

### Verificación del aislamiento

El criterio de seguridad es que un usuario nunca pueda consultar ni modificar datos de otro taller aunque conozca un UUID válido. Las operaciones administrativas reciben el contexto del usuario autenticado y los servicios aplican filtros por `shop_id` en tickets, clientes, inventario y operaciones relacionadas. Las verificaciones de base de datos y endpoints se ejecutan con los scripts descritos en la sección de pruebas; para una auditoría formal todavía sería recomendable convertir estos escenarios en una suite automatizada de regresión.

## Pruebas y verificación

El proyecto cuenta actualmente con scripts de verificación manual y pruebas de integración orientadas a los flujos críticos:

| Script | Propósito |
|---|---|
| `backend/scripts/test_db.py` | Comprobar conexión y estado básico de la base de datos |
| `backend/scripts/test_inventory_endpoint.py` | Verificar `GET` y `POST /inventory`, incluido `is_low_stock` |
| `backend/scripts/test_real_post.py` | Probar la creación de inventario contra una base de datos real |
| `backend/scripts/test_ticket_service.py` | Ejercitar escenarios del servicio de tickets y aislamiento de datos |

Ejecutar desde `backend/`, con el entorno virtual y las variables configuradas:

```bash
python scripts/test_db.py
python scripts/test_inventory_endpoint.py
python scripts/test_real_post.py
python scripts/test_ticket_service.py
```

Para validar el frontend:

```bash
cd frontend
npm run build
npm run lint
```

Estos scripts no sustituyen todavía una suite automatizada ejecutada en CI. La siguiente evolución recomendable es incorporar pytest para el backend, una base de datos de pruebas aislada y pruebas de regresión multi-tenant; en el frontend, añadir pruebas de componentes para formularios, modales y estados de error.

## Documentación del proyecto

TecniDesk se encuentra en una etapa funcional de MVP, con los flujos principales de administración de talleres, tickets, diagnóstico, inventario y tracking público implementados. La documentación complementaria está separada por propósito:

- `PROJECT_STATE.md`: estado técnico, decisiones recientes y contexto para continuar el desarrollo.
- `Gemini.md`: instrucciones operativas y criterios de trabajo del proyecto.
- `AUDITORIA_TECNICA.md`: hallazgos, riesgos y controles revisados durante la auditoría.
- `PLAN_REPARACION_PIN.md`: contexto de la reparación del flujo de PIN.
- `PLAN_WHITELABEL.md`: decisiones del portal con identidad visual del taller.

El README resume el producto y cómo ejecutarlo; estos documentos conservan el detalle histórico y técnico que no es necesario leer para una primera evaluación.

## Licencia

Proyecto desarrollado con fines académicos y de titulación. Actualmente el repositorio no incluye un archivo `LICENSE`, por lo que no se declara una licencia open source ni permisos de redistribución o modificación. La marca TecniDesk, su identidad visual y los datos de cualquier entorno desplegado son propietarios.

Si el repositorio se publica como proyecto open source, debe añadirse una licencia explícita, por ejemplo MIT, y revisar por separado la licencia de assets, documentación y configuraciones de terceros.
