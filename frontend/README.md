# TecniDesk Frontend

**Interfaz de usuario moderna y Workbench Operativo para el Micro SaaS de gestión de talleres de celulares.**

Este proyecto es el cliente web de TecniDesk, desarrollado con **React 19**, **Vite 7** y **Tailwind CSS 4**. Ofrece una experiencia de alta fidelidad visual (*Workbench / Atmospheric*), gestión de estado ultra veloz con **React Query v5**, alternador de vistas (Lista y Tablero Kanban), diagnóstico asistido por IA, protección de privacidad (enmascaramiento de PII) y portal de rastreo público con whitelabeling dinámico.

---

## 🚀 Stack Tecnológico

- **Framework:** React 19
- **Build Tool:** Vite 7
- **Enrutamiento:** React Router 7
- **Estado Asíncrono & Caché:** `@tanstack/react-query` v5
- **Estilos & Diseño:** Tailwind CSS 4 + Variables CSS (Paleta OKLCH ámbar)
- **Iconografía:** `lucide-react`
- **Gestión de Temas:** `ThemeContext` (Modo Claro / Modo Oscuro con persistencia en `localStorage`)
- **Compresión de Imágenes:** `browser-image-compression` (compresión en cliente <800 KB)
- **Testing:** Vitest 3, `@testing-library/react`, `@testing-library/jest-dom`

---

## 🛠️ Instalación y Desarrollo

### 1. Requisitos Previos
- Node.js (v18 o superior)
- npm (o pnpm / yarn)

### 2. Configuración Inicial

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variable de entorno para desarrollo
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### 3. Ejecutar en Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

---

## 📦 Características Principales & Módulos

### 🛠️ Workbench Operativo del Taller (Fases 1 a 5)
- **Alternador de Vista Lista / Tablero Kanban:** Selector interactivo en la barra de herramientas del `AdminDashboard.jsx` con persistencia de preferencia en `localStorage` (`tecnidesk_workbench_view`).
- **Tablero Kanban Interactivo:** Organizado en 5 columnas de flujo operativo (*Ingreso / Recepción*, *En Revisión & Diagnóstico*, *Presupuesto & Espera*, *En Reparación*, *Listo para Retirar*) con tarjetas de alta densidad, badges de técnico y alertas visuales de SLA vencido en rojo.
- **Smart Action CTA:** Botón contextual prioritario (*Asignar* → *Diagnosticar* → *WhatsApp* → *Ver detalle*) para guiar ágilmente al personal del taller.
- **Guardias Técnicas en UI:** Intercepción y feedback visual en cambios de estado para garantizar que no se avance a `EN_REPARACION` sin técnico responsable.
- **Ajustes de SLAs Multi-Tenant (`SlaSettingsModal.jsx`):** Modal interactivo para configurar umbrales de SLA por estado en tiempo real con botón de restablecimiento a valores predeterminados.
- **Métricas de Tiempos de Ciclo (`CycleTimeAnalyticsModal.jsx`):** Visualización de Lead Time, Cycle Time activo, desglose por etapa en barras de progreso y detección gráfica del cuello de botella.

### 👨‍🔧 Portal de Técnico Dedicado (`/tech`)
- **Mesa de Trabajo de Alta Densidad (`TechnicianDashboard.jsx`):** Pestañas "Mis Asignaciones" y "Equipos Disponibles" con auto-asignación en 1 clic y selector de vista Lista vs Tablero Kanban de 3 columnas (*Por Diagnosticar*, *En Reparación / Repuesto*, *Listo para Entrega*).
- **Modo Supervisor para Administradores:** Los usuarios administradores que navegan a `/tech` entran en modo de solo lectura (sin mutaciones operativas ni emisión de PINs) para preservar la trazabilidad de auditoría.
- **Ficha de Reparación Ágil (`TechnicianWorkModal.jsx`):** Desbloqueo seguro de PIN/patrón auditado con toggle `Eye`/`EyeOff`, transiciones de estado de 1 clic, vinculación de repuestos y evidencias fotográficas.
- **Copiloto IA Técnico (`AiChatBubble.jsx` y `AiChatDrawer.jsx`):** Burbuja flotante permanente en `/tech` y drawer lateral conversacional potenciado por Gemini 3.7 Flash con soporte para consulta libre y diagnóstico contextualizado al ticket.

### 🧠 Diagnóstico Asistido con IA (`DiagnosticAssistPanel.jsx`)
- Panel de razonamiento explicable integrado en el modal de diagnóstico (`DiagnosticModal.jsx`).
- Sugerencias generadas por IA con citaciones grounding, evaluación de confianza y selector rápido de repuestos comunes.
- Interfaz interactiva de feedback y confirmación de aprendizaje RAG para enriquecer la base de conocimiento (`pgvector`).

### 🔒 Privacidad y Enmascaramiento de PII
- Módulo `src/utils/privacy.js` (`maskPhone`, `maskEmail`, `maskTrackingCode`) para evitar *shoulder surfing* en mostrador.
- Enmascaramiento por defecto en tarjetas del panel y botón de revelado seguro (`Eye`/`EyeOff`) dentro de `AdminTicketCard.jsx` y `TechnicianWorkModal.jsx`.

### 🎨 Arquitectura de Temas (Modo Claro & Modo Oscuro)
- Paleta cálida ámbar construida sobre espacios de color **OKLCH** libre de gradientes sucios.
- Alternador dinámico `ThemeToggle.jsx` conectado a `ThemeContext` y `localStorage` (`tecnidesk-theme`).
- Componente de navegación *N5 Floating Pill* optimizado para pantallas de taller.

### 🔍 Portal de Rastreo Público & Whitelabeling
- Consulta sin credenciales mediante `tracking_token` auto-generado.
- Adaptación dinámica de marca (nombre del taller y logotipo).
- Autorización o rechazo interactivo de presupuestos con motivo opcional.
- Botón contextual de WhatsApp para negociación directa de costos.

### ⚡ Caché Zero-Delay
- Carga instantánea de detalles de órdenes usando `initialData` de React Query.
- Purgado seguro de memoria en eventos de cierre de sesión (`auth:logout` ejecutando `queryClient.clear()`).

---

## 🧪 Pruebas Automatizadas (Vitest + Testing Library)

El frontend cuenta con una suite automatizada completa que valida componentes, modales, vistas Kanban, portal de técnico, copiloto IA, utilidades y hooks:

```bash
# Ejecutar todas las pruebas (97 tests pasando al 100%)
npm test

# Ejecutar pruebas con reporte de cobertura
npm run test:coverage

# Ejecutar pruebas en modo observador (watch)
npx vitest
```

---

## 📂 Estructura de Carpetas

```text
frontend/
├── src/
│   ├── api/                   # Cliente fetch autenticado (`authFetch.js`), tickets, diagnostic, technician
│   ├── assets/                # Recursos estáticos (logos, iconografía)
│   ├── components/            # Componentes globales y de protección
│   │   ├── guards/            # ProtectedRoute (con matriz de roles) y PublicRoute
│   │   └── shared/            # ThemeToggle, Logo, Steppers, etc.
│   ├── context/               # ThemeContext (Modo Claro / Oscuro)
│   ├── features/              # Módulos principales:
│   │   ├── admin/             # Workbench Administrativo y Analítica
│   │   │   ├── components/    # KanbanBoard, SlaSettingsModal, CycleTimeModal, etc.
│   │   │   └── AdminDashboard.jsx
│   │   ├── technician/        # Portal de Técnico, Mesa de Trabajo y Copiloto IA
│   │   │   ├── AiChatBubble.jsx
│   │   │   ├── AiChatDrawer.jsx
│   │   │   ├── TechnicianHeader.jsx
│   │   │   ├── TechnicianTicketCard.jsx
│   │   │   ├── TechnicianWorkModal.jsx
│   │   │   └── TechnicianDashboard.jsx
│   │   └── tracking/          # Portal público de rastreo
│   ├── pages/                 # Páginas (Login, Registro, Recuperación de contraseña)
│   ├── tests/                 # 97 pruebas automatizadas (Vitest)
│   ├── utils/                 # Utilidades (privacy.js, date.js, currency.js, constants.js)
│   ├── App.css                # Estilos globales, paleta OKLCH y diseño Workbench
│   ├── App.jsx                # Enrutador principal y configuración de React Query
│   ├── index.css              # Punto de entrada Tailwind CSS 4
│   └── main.tsx               # Montaje del árbol React
├── public/                    # Archivos estáticos públicos
├── package.json
└── vite.config.ts
```

---

## 🎨 Guía de Estilo y Paleta OKLCH

- **Primary / Amber Accent:** Tono ámbar cálido calibrado en OKLCH para botones primarios, estados activos y badges de SLA.
- **Success / WhatsApp:** `#25D366` para indicadores de éxito y contacto de WhatsApp.
- **Atmospheric Dark:** Tema oscuro profundo diseñado para reducir fatiga visual en mostradores y talleres.
- **Warm Light:** Tema claro de alto contraste basado en fondos crema/ámbar sutiles (`[data-theme="light"]`).

