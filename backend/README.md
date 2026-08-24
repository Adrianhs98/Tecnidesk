# TecniDesk Backend API

**Micro SaaS Multi-Tenant** para gestión de talleres de reparación de celulares — Mercado Ecuatoriano.

Este backend proporciona una API REST asíncrona, robusta y segura construida con **FastAPI** y **SQLAlchemy 2.0**, diseñada para gestionar el ciclo de vida completo de las órdenes de servicio, diagnóstico asistido por IA mediante RAG híbrido, analítica de tiempos de ciclo y portal de rastreo público para clientes.

---

## 🚀 Stack Tecnológico

- **Framework:** FastAPI (Python 3.12+)
- **ORM & Persistencia:** SQLAlchemy 2.0 (Patrones asíncronos) + `asyncpg` sobre PostgreSQL
- **Búsqueda Vectorial & RAG:** Extensión `pgvector` con índices HNSW (768 dimensiones)
- **Modelos de IA:** Google Gemini 3.7 Flash (razonamiento explicable grounded) + Ollama (`nomic-embed-text-v2-moe`)
- **Migraciones:** Alembic
- **Seguridad & Criptografía:** JWT (Access Tokens y Refresh Tokens con rotación estatal), Fernet (cifrado simétrico de PINs/contraseñas), Bcrypt (hashing de passwords)
- **Validación & Configuración:** Pydantic v2 y Pydantic Settings
- **Rate Limiting:** SlowAPI
- **Almacenamiento Cloud:** Cloudflare R2 (API S3 compatible)
- **Email Transaccional:** Resend

---

## 🛠️ Instalación y Configuración

### 1. Clonar e instalar dependencias

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y completa las variables de entorno:

```bash
cp .env.example .env
```

Variables clave requeridas:
- `DB_URL`: Conexión asíncrona a PostgreSQL (`postgresql+asyncpg://...`).
- `DATABASE_URL`: Conexión síncrona opcional para CLI y Alembic.
- `JWT_SECRET` / `JWT_REFRESH_SECRET`: Secretos para la emisión de tokens JWT.
- `FERNET_KEY`: Clave de cifrado simétrico para contraseñas de dispositivos.
- `GEMINI_API_KEY`: API Key de Google Gemini para diagnóstico asistido.
- `LOCAL_EMBEDDING_SERVICE_URL`: URL base de Ollama (ej. `http://localhost:11434`).
- `R2_ENDPOINT`, `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET_NAME`: Almacenamiento de evidencias.

### 3. Base de Datos y Migraciones

```bash
# Aplicar migraciones con Alembic
alembic upgrade head

# Poblar datos iniciales (Planes, etc.)
python scripts/seed.py
```

### 4. Iniciar Servidor de Desarrollo

```bash
uvicorn app.main:app --reload --port 8000
```

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`

---

## 🔒 Características Principales & Arquitectura

### 🏢 Aislamiento Multi-Tenant (Seguridad C1)
Cada taller opera estrictamente bajo su `shop_id`. Las dependencias (`get_current_user`, `subscription_guard`, `admin_guard`) resuelven la identidad del inquilino, y todos los servicios (`TicketService`, `ShopService`, etc.) filtran obligatoriamente las consultas y mutaciones por dicho identificador.

### 🛠️ Workbench Operativo del Taller (Fases 1 a 5)
- **Ordenamiento SQL Inteligente:** Priorización en base de datos (`CASE`) que prioriza tickets sin técnico asignado (`technician_id IS NULL`), seguidos de tickets con SLA vencido y orden cronológico descendente.
- **Guardia Estricta de Asignación:** Bloqueo en `TicketService` que lanza `UnassignedTechnicianError` (HTTP 400) al intentar pasar a `EN_REPARACION` sin técnico responsable.
- **Auditoría Inmutable de Estados:** Registro síncrono en `ticket_status_history` de cada cambio de estado con autor, timestamp y motivo.
- **SLAs Multi-Tenant Configurables:** Persistencia de umbrales por tienda en `shops.sla_config` (`GET/PATCH /shops/sla-config`) con fallback a `DEFAULT_SLA_THRESHOLDS_HOURS`.
- **Analítica de Tiempos de Ciclo (`GET /tickets/analytics/cycle-times`):** Cálculo automatizado de Lead Time (ingreso a entrega), Cycle Time activo, tiempo medio por etapa y detección del cuello de botella principal del taller.

### 🧠 Diagnóstico Asistido con RAG Híbrido & Human-in-the-Loop
- **Embeddings y Búsqueda Vectorial:** Integración de `pgvector` con índices HNSW sobre 768 dimensiones para recuperación semántica contextualizada por tienda.
- **Razonamiento Grounded:** Servicio de explicación técnica asistido por Gemini 3.7 Flash con validación anti-alucinación.
- **Corrección Interactiva y Aprendizaje:** Endpoint de feedback que permite al técnico ajustar diagnósticos y guardar casos reales validados (`real_validated`).

### 📱 Gestión de Tickets & Cifrado de Dispositivos
- **Cifrado Fernet:** Los PINs o patrones de desbloqueo se cifran simétricamente antes de persistirse y se desencriptan únicamente en la capa interna de servicios.
- **Evidencias en R2:** Carga segura de evidencias fotográficas vinculadas a la orden.
- **Rastreo Público:** Endpoint `/tracking/{token}` sin requerir sesión para consulta del cliente.

### 👨‍🔧 Gestión de Técnicos & Portal Dedicado
- **Perfil Seguro del Técnico (`GET /technicians/me`):** Whitelist estricto de campos operativos sin exponer datos financieros del taller.
- **Auto-asignación de Reparaciones (`POST /tickets/{id}/assign-me`):** Permite a los técnicos tomar equipos disponibles directamente.
- **Revelado Seguro de PIN con Auditoría (`POST /tickets/{id}/reveal-pin`):** Desencriptación bajo demanda protegida con rate limit de 15/min y registro en `ticket_status_history`.
- **Copiloto IA Técnico (`POST /diagnostic/chat` y `POST /tickets/{id}/diagnostic-chat`):** Asistencia técnica conversacional libre o atada a una orden, con guard de ownership `verify_ticket_technician_access` y SlowAPI con clave por `user_id`.
- **Sincronización de Usuarios (`scripts/sync_technicians_users.py`):** Script para enlazar técnicos con cuentas de usuario `technician`.

---

## 🧪 Pruebas Automatizadas (Testing Suite)

El backend cuenta con una suite automatizada con **pytest** y **respx** para mocks HTTP asíncronos:

```bash
# Ejecutar toda la suite (130 tests pasando al 100%)
pytest

# Ejecutar suite con reporte de cobertura de código
pytest --cov=app tests/

# Ejecutar pruebas de integración
pytest tests/integration/

# Ejecutar pruebas unitarias
pytest tests/unit/
```

---

## 📂 Estructura del Proyecto

```text
backend/
├── alembic/              # Control de versiones y migraciones de BD
├── app/
│   ├── api/v1/           # Endpoints públicos (tracking)
│   ├── core/             # Dependencias, JWT, guards de seguridad y rate limiters (SlowAPI)
│   ├── models/           # Modelos ORM SQLAlchemy 2.0
│   ├── routers/          # Controladores FastAPI (Auth, Tickets, Shops, Technicians, Diagnostic, etc.)
│   ├── schemas/          # Modelos Pydantic v2 para validación I/O
│   ├── services/         # Servicios de lógica de negocio (TicketService, EmbeddingService, etc.)
│   ├── config.py         # Configuración centralizada vía Pydantic Settings
│   ├── database.py       # Motor asíncrono y sesión SQLAlchemy
│   └── main.py           # Aplicación FastAPI, configuración de CORS y middlewares
├── scripts/              # Seeds y scripts operativos (sync_technicians_users.py)
├── tests/                # 130 pruebas unitarias y de integración (pytest)
├── requirements.txt      # Dependencias de Python
└── alembic.ini           # Configuración de Alembic
```

---

## 🛡️ Decisiones de Diseño

- **Refresh Tokens Stateful:** Los tokens de refresco se persisten en base de datos con hash SHA-256 para permitir revocación inmediata en logout.
- **Control de Suscripción:** Middleware `subscription_guard` que bloquea accesos con `HTTP 402 Payment Required` ante suscripciones vencidas.
- **Rollback Transaccional:** La dependencia asíncrona `get_db` garantiza rollback automático ante cualquier excepción no controlada.
- **Manejo Global de Excepciones:** `global_exception_handler` en `main.py` genera un `request_id` trazable y preserva los headers de CORS ante errores imprevistos.

