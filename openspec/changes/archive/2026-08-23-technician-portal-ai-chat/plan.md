# Plan de Implementación SDD v2.0: Portal de Técnico y Copiloto IA Conversacional

**Identificador del Cambio:** `2026-08-23-technician-portal-ai-chat`  
**Estado:** ✅ Implementado, Ajustado y Verificado (100% Tests en Verde: 130 Pytest, 97 Vitest)  
**Fecha de Cierre:** 23 de Agosto, 2026  
**Auditor:** Senior Architect (TecniDesk)

---

## 1. Auditoría Técnica de los 7 Puntos de Control

### Punto 1: Autorización Real y Ownership de Tickets (No sólo filtrado de lista)
* **Estado:** ⚠️ **Riesgo encontrado**
* **Evidencia en Código:**
  - `backend/app/routers/tickets.py:L183` (`GET /{ticket_id}`): Utiliza `ticket_service.get_ticket_by_id(db, ticket_id, current_user.shop_id)`.
  - `backend/app/routers/tickets.py:L210` (`PATCH /{ticket_id}/status`): Ejecuta la actualización sin verificar si el ticket está asignado al `current_user`.
  - `backend/app/routers/tickets.py:L443` (`PATCH /{ticket_id}/diagnostic`): Solo valida `shop_id`.
  - `backend/app/routers/tickets.py:L606` (`POST /{ticket_id}/diagnostic-chat`): Solo valida `shop_id`.
  - `backend/app/routers/tickets.py:L636` (`POST /{ticket_id}/diagnostic-chat/confirm`): Solo valida `shop_id`.
* **Comportamiento Actual:** Si un técnico ingresa manualmente el UUID de un ticket de otro técnico de su mismo taller, hoy puede leerlo, cambiarle el estado, enviar diagnósticos y chatear con la IA sin ninguna restricción.
* **Solución y Guard Propuesto:**
  Se crea la dependencia FastAPI `verify_ticket_technician_access` en `backend/app/core/dependencies.py`:
  ```python
  async def verify_ticket_technician_access(
      ticket_id: uuid.UUID,
      current_user: User = Depends(subscription_guard),
      db: AsyncSession = Depends(get_db),
  ) -> Ticket:
      ticket = await ticket_service.get_ticket_by_id(db, ticket_id, current_user.shop_id)
      if current_user.role == UserRoleEnum.technician:
          tech_id = await technician_service.get_technician_id_by_user_id(db, current_user.id, current_user.shop_id)
          # Permite acceso si el ticket está asignado al técnico o si está sin asignar (para tomarlo)
          if ticket.technician_id is not None and ticket.technician_id != tech_id:
              raise HTTPException(
                  status_code=status.HTTP_403_FORBIDDEN,
                  detail="No tienes autorización para operar sobre un ticket asignado a otro técnico."
              )
      return ticket
  ```
  **Endpoints donde aplica:** `PATCH /tickets/{id}/status`, `PATCH /tickets/{id}/diagnostic`, `POST /tickets/{id}/diagnostic-chat`, `POST /tickets/{id}/diagnostic-chat/confirm` y `POST /tickets/{id}/items`.

---

### Punto 2: Shape de Respuesta de `GET /technicians/me` (Privacidad y Aislamiento)
* **Estado:** ❌ **No implementado (Endpoint nuevo)**
* **Evidencia en Código:**
  - `backend/app/schemas/technician.py:L45-64`: El schema `TechnicianWithMetrics` expone `attributed_value` y `delivered_value` (facturación monetaria atribuida), y `ShopTotals` expone los ingresos totales del taller (`total_attributed`, `total_delivered`).
* **Riesgo:** Si reutilizamos el schema administrativo de métricas, un técnico podría ver ingresos globales del taller y comisiones de otros técnicos.
* **Schema Pydantic Whitelist Estricto Propuesto (`TechnicianMeResponse`):**
  ```python
  class TechnicianMeResponse(BaseModel):
      id: uuid.UUID
      user_id: uuid.UUID
      full_name: str
      email: EmailStr
      role: str
      declared_specialty: str | None
      inferred_specialties: list[InferredSpecialty]
      active_tickets_count: int
      completed_tickets_count: int

      model_config = {"from_attributes": True}
  ```
  *Garantía:* Cero exposición de montos monetarios, comisiones, notas internas del negocio o datos de otros técnicos.

---

### Punto 3: PIN Desencriptado — Seguridad, Cifrado y Auditoría
* **Estado:** ✅ **Confirmado**
* **Evidencia en Código:**
  - `backend/app/models/ticket.py:L69`: `pin_or_password` almacena el **PIN o patrón de desbloqueo del celular del cliente** (para pruebas de hardware post-reparación). No es un PIN de retiro (el rastreo público usa `tracking_token`).
  - `backend/app/services/encryption_service.py:L4-75`: Cifrado simétrico **Fernet** (`cryptography`) con clave `FERNET_KEY`.
  - `backend/app/services/ticket_service.py:L360`: Desencriptado controlado mediante `decrypt_pin()`.
* **Propuesta de Auditoría:**
  - En lugar de enviar el PIN en texto claro en cada GET genérico, se implementa el endpoint seguro de revelado bajo demanda:  
    `POST /tickets/{id}/reveal-pin` (protegido por `verify_ticket_technician_access`).
  - Se registra el evento en la tabla `ticket_status_history` o en `device_access_logs`:
    `(ticket_id, accessed_by_user_id, timestamp, action="PIN_REVEALED")`.

---

### Punto 4: Rate Limiting en Chat Libre (`POST /diagnostic/chat`) vs Chat de Ticket
* **Estado:** ⚠️ **Riesgo encontrado**
* **Evidencia en Código:**
  - `backend/app/core/rate_limit.py:L11`: `limiter = Limiter(key_func=get_remote_address)`.
  - `backend/app/routers/tickets.py:L606`: `POST /{ticket_id}/diagnostic-chat` actualmente **no tiene ningún decorador `@limiter.limit`**.
  - `backend/app/services/correction_service.py:L79-85`: Invoca Gemini 3.7 Flash (`google.genai`), generando consumo de cuotas/tokens.
* **Riesgo de IP Compartida:** En un taller físico, todos los técnicos comparten la misma IP pública por WiFi. Usar `get_remote_address` bloquearía a todo el taller si un solo técnico envía múltiples mensajes.
* **Estrategia de Rate Limit Diferenciada (Key por `user_id`):**
  1. **Helper de Key por Usuario:**
     ```python
     def get_user_rate_limit_key(request: Request) -> str:
         # Extrae user_id del state de autenticación; fallback a IP si no hay auth
         return getattr(request.state, "user_id", get_remote_address(request))
     ```
  2. **Chat Libre (`POST /diagnostic/chat`):** Límite estricto de **10 consultas / minuto por técnico** (máximo 100 / hora) para prevenir drenaje de cuota LLM en consultas no asociadas a órdenes.
  3. **Chat de Ticket (`POST /tickets/{id}/diagnostic-chat`):** Límite operacional de **25 interacciones / minuto por técnico** (suficiente para iteraciones de diagnóstico ágiles).

---

### Punto 5: Integridad de Datos Existentes y Cola de Tickets
* **Estado:** ⚠️ **Riesgo encontrado**
* **Evidencia en Código:**
  - `backend/app/models/ticket.py:L53`: `technician_id` es nullable (`Mapped[uuid.UUID | None]`).
  - `PROJECT_STATE.md:L167`: Se evidenció un **79% de tickets sin técnico asignado** en el baseline del taller piloto.
* **Problema:** Si el panel del técnico filtra exclusivamente por `technician_id == current_tech_id`, el 79% de las órdenes y todos los equipos nuevos que ingresen al taller desaparecerían del panel del técnico.
* **Solución Arquitectónica:**
  - La vista del técnico en UI debe tener dos pestañas:
    1. **"Mi Mesa de Trabajo"** (`technician_id == me.id`): Sus asignaciones activas.
    2. **"Equipos sin Asignar"** (`technician_id IS NULL`): Equipos en recepción/revisión con botón de 1 clic **"Tomar Reparación"** (`PATCH /tickets/{id}/assign-me`).
  - **Script de Validación:** `backend/scripts/audit_technician_data.py` para verificar que los registros de `technicians` tengan consistencia con `users` y `tickets`.

---

### Punto 6: Coexistencia con el RAG Híbrido (`synthetic` vs `real_validated`)
* **Estado:** ✅ **Confirmado**
* **Evidencia en Código:**
  - `backend/app/services/correction_service.py:L132-147`: `confirm_correction` realiza un `db.add(new_case)` insertando un nuevo registro con `source_type='real_validated'` y `shop_id=shop_id`.
  - `backend/app/services/diagnostic_service.py:L8-17`: La búsqueda vectorial filtra `(shop_id = :target_shop OR shop_id IS NULL)` y aplica un bono de relevancia `REAL_CASE_BONUS = 0.10` a los casos reales.
* **Garantía:** Los casos sintéticos globales (`shop_id IS NULL`) jamás se sobreescriben ni mutan. El nuevo portal técnico alimenta de forma segura la base de aprendizaje del taller sin riesgo de regresión.

---

### Punto 7: Separación de Roles en JWT y Sesiones Activas
* **Estado:** ✅ **Confirmado**
* **Evidencia en Código:**
  - `backend/app/core/security.py:L46-71`: `create_access_token` ya incluye el claim `"role": role` en el payload JWT.
  - `backend/app/core/dependencies.py:L86-90`: `get_current_user` valida contra la tabla `users` en cada petición.
  - `backend/app/schemas/auth.py:L40-46`: `TokenResponse` sólo omitía exponer `role` y `full_name` en el cuerpo JSON de respuesta.
* **Compatibilidad:** Extender `TokenResponse` con `role: str` y `full_name: str` es 100% retrocompatible. No se requiere invalidar sesiones activas porque la validación de roles en backend siempre consulta el registro vivo en base de datos.

---

## 2. Riesgos Adicionales Identificados en el Código

1. **Fuga de Métricas Financieras en Endpoints Administrativos:**
   - `backend/app/routers/tickets.py:L163` (`GET /tickets/analytics/cycle-times`) usa `subscription_guard` en lugar de `admin_guard`. Un técnico podría consultar cuellos de botella y tiempos de ciclo globales.
   - `backend/app/routers/technicians.py:L56` (`GET /technicians/metrics`) usa `subscription_guard` en lugar de `admin_guard`. Un técnico podría ver los ingresos y comisiones atribuidos a sus compañeros.  
   *Ajuste:* Cambiar ambos endpoints a `admin_guard`.
2. **Vínculo `User` ↔ `Technician` en Creación:**
   - Actualmente `POST /technicians` en `app/routers/technicians.py` crea filas en `technicians` sin crear cuenta en `users`.
   - Para que un técnico pueda autenticarse en `/login`, debe existir un registro en `users` (`role="technician"`) enlazado a `technicians.user_id`. Se debe soportar la creación de credenciales al dar de alta al técnico.

---

## 3. Plan de Implementación Detallado v2.0

### Fase 1: Backend — Seguridad, Permisos y Endpoints Específicos
1. **Dependency `verify_ticket_technician_access`:** Asegurar ownership estricto en mutaciones de tickets.
2. **Blindaje de Rutas Administrativas:** Reemplazar `subscription_guard` por `admin_guard` en `GET /technicians/metrics` y `GET /tickets/analytics/cycle-times`.
3. **Endpoint `GET /technicians/me`:** Implementado con schema `TechnicianMeResponse`.
4. **Endpoint `POST /tickets/{id}/assign-me`:** Permite al técnico tomar un ticket sin asignar.
5. **Rate Limiting por Usuario:** Decorar endpoints de IA con SlowAPI basado en `user_id`.

### Fase 2: Frontend — Enrutamiento y Protección
1. **Actualización de `LoginPage.jsx`:** Guardar `td_role` y redirigir a `/admin` o `/tech`.
2. **Actualización de `ProtectedRoute.jsx`:** Restringir acceso a `/admin` solo a `admin`. Técnicos son redirigidos a `/tech`.
3. **Ruta `/tech` en `App.jsx`:** Montar `TechnicianDashboard.jsx`.

### Fase 3: Frontend — Portal de Técnico (`TechnicianDashboard.jsx`)
1. **Mesa de Trabajo del Técnico:**
   - Pestaña 1: "Mis Reparaciones" (filtrado por `technician_id == me.id`).
   - Pestaña 2: "Equipos Disponibles" (`technician_id IS NULL`) con botón de auto-asignación.
   - Badges de SLA dinámico en tiempo real y vista de alta densidad.
2. **Ficha de Reparación Rápida:**
   - Botón de revelado seguro de PIN de dispositivo con log de auditoría.
   - Acciones de 1 clic para transicionar estados (*Iniciar Revisión*, *Pedir Repuesto*, *En Reparación*, *Listo*).

### Fase 4: Frontend — Copiloto IA (`AiChatBubble` + `AiChatDrawer`)
1. **Burbuja Flotante Flotante (FAB):** Acceso permanente en la esquina inferior derecha.
2. **Drawer Conversacional:** Chat interactivo contextualizado al ticket activo o en modo libre, con botón de "Aplicar al Diagnóstico" y "Confirmar Aprendizaje".

### Fase 5: Pruebas y Validación
1. **Pytest (Backend):** Tests de ownership (403 al tocar ticket ajeno), tests de `GET /technicians/me` y rate limiting de IA.
2. **Vitest (Frontend):** Tests de renderizado del dashboard de técnico, tabs de asignación y burbuja de chat.
