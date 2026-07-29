# TecniDesk Backend API

**Micro SaaS Multi-Tenant** para gestión de talleres de reparación de celulares — Mercado Ecuatoriano.

Este backend proporciona una API robusta y segura para gestionar el ciclo de vida de las reparaciones, desde el ingreso del equipo hasta la entrega, con un portal de rastreo público para clientes finales.

## 🚀 Stack Tecnológico

- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0 (Patrones asíncronos)
- **Base de Datos:** PostgreSQL con `asyncpg`
- **Migraciones:** Alembic
- **Seguridad:** JWT (Access/Refresh Tokens), Fernet (Cifrado de PINs), Bcrypt (Passwords)
- **Validación:** Pydantic v2
- **Rate Limiting:** SlowAPI

---

## 🛠️ Instalación y Configuración

### 1. Clonar e instalar dependencias

```bash
# Clonar el repositorio
git clone <repo-url>
cd tecnidesk-backend

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copia el archivo `.env.example` a `.env` y completa las variables:

```bash
copy .env.example .env
```

Variables críticas:
- `DB_URL`: Conexión asíncrona a PostgreSQL.
- `JWT_SECRET`: Clave para tokens de acceso.
- `FERNET_KEY`: Clave para cifrar contraseñas de dispositivos.

### 3. Base de Datos y Seed

```bash
# Aplicar migraciones
alembic upgrade head

# Poblar datos iniciales (Planes, etc.)
python scripts/seed.py
```

### 4. Iniciar Servidor

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 🔒 Características Principales

### 🏢 Multi-Tenant (Seguridad C1)
Cada taller tiene su propio `shop_id`. La lógica de servicios garantiza que un taller nunca pueda acceder a los datos de otro mediante filtrado forzado en la capa de negocio.

### 📱 Gestión de Tickets
- **Cifrado de Seguridad:** Los PINs o patrones de desbloqueo de los clientes se guardan cifrados con Fernet.
- **Evidencias:** Soporte para registro de fotos del estado del equipo.
- **Rastreo Público:** Endpoint especializado `/tracking/{token}` que permite a clientes ver el progreso sin necesidad de login.
- **Asignación de Técnicos:** Asignación manual o balanceo automático de carga basado en la cantidad de tickets activos por técnico.

### 👨‍🔧 Gestión de Técnicos
- **Métricas y Especialidades:** El backend analiza dinámicamente el texto de los diagnósticos y repuestos para inferir las áreas de expertise del técnico, calculando además ingresos proxy generados por el técnico en tiempo real.

### 💬 Integración WhatsApp y Negociación
El sistema captura el número de contacto del taller durante el registro (`contact_whatsapp`) y lo expone de manera segura en el portal de rastreo, activando un canal contextualizado para negociar y revisar presupuestos directamente con el cliente.

---

## 📂 Estructura del Proyecto

- `app/main.py`: Punto de entrada y configuración de Middlewares (CORS, Rate Limit).
- `app/models/`: Definición de tablas con SQLAlchemy 2.0.
- `app/services/`: Capa de lógica de negocio (TicketService, AuthService).
- `app/routers/`: Definición de endpoints FastAPI.
- `app/schemas/`: Modelos Pydantic para validación de entrada/salida.

---

## 🛡️ Decisiones de Diseño

- **Refresh Tokens Stateful:** Los tokens de refresco se guardan en la DB (hash SHA-256) para permitir revocación inmediata (Logout).
- **Subdominios Dinámicos:** Cada taller recibe un subdominio único validado por Regex.
- **Rollback Automático:** La dependencia `get_db` asegura que cualquier error no controlado haga rollback de la transacción.
