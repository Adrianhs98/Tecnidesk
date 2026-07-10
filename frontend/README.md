# TecniDesk Frontend

**Interfaz de usuario moderna para el Micro SaaS de gestión de talleres de celulares.**

Este proyecto es el frontend de TecniDesk, desarrollado con un enfoque en la velocidad, la experiencia de usuario (UX) y la facilidad de uso tanto para administradores de talleres como para sus clientes finales.

## 🚀 Stack Tecnológico

- **Framework:** React 19
- **Build Tool:** Vite 7
- **Lenguaje:** JavaScript / TypeScript (tipado progresivo)
- **Routing:** React Router (v7)
- **Estilos:** Tailwind CSS v4 + Variables CSS (Modern UI)
- **Comunicación:** Fetch API con interceptores para JWT

---

## 🛠️ Instalación y Desarrollo

### 1. Requisitos
- Node.js (v18 o superior)
- npm o yarn

### 2. Configuración inicial

```bash
# Clonar el repositorio
git clone <repo-url>
cd tecnidesk-frontend

# Instalar dependencias
npm install
```

### 3. Ejecutar en desarrollo

```bash
npm run dev
```
La aplicación estará disponible en `http://localhost:5173` por defecto.

---

## 📦 Características Principales

### 🔧 Portal de Administración
- **Dashboard:** Vista general de tickets activos, por reparar y listos.
- **Gestión de Tickets:** Creación de órdenes de reparación, carga de evidencias (fotos) y diagnóstico técnico.
- **Control de Estados:** Actualización fluida del ciclo de vida del equipo (En revisión, Esperando repuesto, Listo, etc.).

### 🔍 Portal de Rastreo Público
- Acceso mediante token único (sin login para el cliente).
- Visualización en tiempo real del progreso de la reparación.
- **Whitelabeling Dinámico:** El portal adapta el nombre de la tienda y su logotipo.
- **Aprobación de Presupuesto:** El cliente puede aceptar o rechazar presupuestos directamente desde el portal.
- **Canal de Negociación (WhatsApp):** Botón contextual unificado que permite al cliente negociar o conversar directamente sobre el presupuesto con el taller asignado.

### 🔐 Seguridad y Auth
- Sistema de registro de talleres con onboarding completo.
- Protección de rutas (Guards) para áreas administrativas.
- Manejo automático de Access y Refresh Tokens.

---

## 📂 Estructura de Carpetas

- `src/api/`: Configuración de la base URL e interceptores de autenticación.
- `src/components/`: Componentes compartidos (Logo, Stepper, Modales).
- `src/features/admin/`: Lógica y componentes exclusivos del panel de administración.
- `src/pages/`: Vistas principales (Login, Registro, Portal de Tracking).
- `src/utils/`: Funciones de ayuda y constantes (formateo de fechas, config de estados).

---

## 🎨 Guía de Estilo

El proyecto utiliza una paleta de colores profesional y moderna:
- **Accent (Dorado):** `#C9A76A` (Primario para botones y estados destacados).
- **Success (Verde):** `#25D366` (WhatsApp e indicadores de éxito).
- **Background:** Diseño oscuro/premium optimizado para visibilidad en talleres.
