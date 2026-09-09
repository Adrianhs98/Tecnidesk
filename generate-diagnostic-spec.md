# Spec: Flujo "Generar diagnóstico" (Ohm)

## Problema actual
El botón **"Aplicar diagnóstico"** puede dispararse desde *cualquier* mensaje del bot en el chat de un ticket. Eso permite que una respuesta parcial o exploratoria ("revisa el pin de carga") termine mostrada al cliente como si fuera el diagnóstico final.

## Objetivo
Separar "conversar con Ohm" de "publicar el diagnóstico al cliente", agregando un paso intermedio de síntesis controlada.

## Flujo propuesto
1. El técnico conversa libremente con Ohm en el chat del ticket (sin cambios).
2. Cuando la reparación está terminada, el técnico presiona **"Generar diagnóstico"**.
   - Dispara `POST /tickets/{id}/generate-diagnostic`.
   - El backend toma **todo el historial de chat de ese ticket** (ya aislado por ticket+técnico+tienda) y lo envía con un prompt de síntesis dedicado.
   - El resultado se guarda en un campo nuevo, **no visible al cliente todavía**: `draft_diagnostic`.
3. El técnico revisa el `draft_diagnostic` (mismo panel donde hoy ve el diagnóstico) y presiona **"Aplicar diagnóstico"**.
   - Este botón deja de aceptar texto libre del frontend. Solo copia `draft_diagnostic` → el campo público (`diagnostic` / el que ya lee el portal de tracking).
4. **"Aprender en RAG"** no cambia — sigue siendo un flujo independiente de guardado de casos validados.

## Cambios de backend

### Modelo (`Ticket`)
Agregar columna:
```python
draft_diagnostic: Mapped[str | None] = mapped_column(Text, nullable=True)
```
Migración Alembic nueva (siguiendo el patrón de tus migraciones existentes, ej. `b3c4d5e6f7a8`).

### Servicio nuevo (`diagnostic_service.py` o donde viva la lógica de Ohm)
```python
async def generate_final_diagnostic(ticket_id: UUID, db: AsyncSession, shop_id: UUID) -> str:
    ticket = await get_ticket_or_404(ticket_id, shop_id, db)
    history = await get_diagnostic_chat_history(ticket_id, db)  # ya existe para el chat

    synthesis_prompt = build_synthesis_prompt(ticket, history)
    result = await gemini_client.aio.models.generate_content(
        model=REASONING_MODEL,  # gemini-3.6-flash — es la respuesta final, no un query rápido
        contents=synthesis_prompt,
    )

    ticket.draft_diagnostic = result.text
    await db.commit()
    return result.text
```

`build_synthesis_prompt` debe instruir explícitamente:
- Redactar el diagnóstico **para el cliente final**, no para el técnico (tono claro, sin jerga interna).
- Basarse solo en lo confirmado/concluido en la conversación, no en hipótesis descartadas.
- No inventar datos que no aparezcan en el historial.

### Endpoint (`routers/tickets.py`)
```python
@router.post("/tickets/{ticket_id}/generate-diagnostic", response_model=DraftDiagnosticResponse)
async def generate_diagnostic(
    ticket_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    verify_ticket_technician_access(ticket_id, current_user)  # guard que ya usas en reveal-pin
    text = await generate_final_diagnostic(ticket_id, db, current_user.shop_id)
    return DraftDiagnosticResponse(draft_diagnostic=text)
```

**Gating de estado** — decide uno (recomiendo A por simplicidad, ajustable):
- **A.** Sin restricción de estado: el técnico puede generarlo cuando quiera, se asume que solo lo hará al terminar. Más simple, confía en el criterio del técnico.
- **B.** Solo permitido si `ticket.status in (EN_REPARACION, LISTO_PARA_RETIRAR)`, devolviendo 400 si se intenta antes (ej. en `EN_REVISION`). Más estricto, evita generar diagnósticos prematuros.

*(Dime cuál prefieres y lo dejo fijo en el endpoint — es el único punto de este spec que depende de una decisión tuya.)*

### Endpoint "Aplicar diagnóstico" (existente — modificar)
Cambiar el schema de entrada: hoy probablemente acepta `{ diagnostic: str }` desde el frontend. Pasa a no aceptar texto:
```python
@router.post("/tickets/{ticket_id}/apply-diagnostic")
async def apply_diagnostic(ticket_id: UUID, ...):
    ticket = await get_ticket_or_404(ticket_id, shop_id, db)
    if not ticket.draft_diagnostic:
        raise HTTPException(400, "No hay un diagnóstico generado para aplicar.")
    ticket.diagnostic = ticket.draft_diagnostic  # el campo que lee el portal público
    ticket.diagnostic_applied_at = datetime.utcnow()
    await db.commit()
```
Esto cierra la puerta a nivel de API, no solo de UI — aunque alguien manipule el frontend, no puede aplicar texto arbitrario.

## Cambios de frontend

- **Botón "Generar diagnóstico"**: nuevo, en `TechnicianWorkModal.jsx` o `AiChatDrawer.jsx` (donde ya viven los otros dos). Llama al nuevo endpoint, muestra loading, y al volver renderiza `draft_diagnostic` en un área de revisión (editable u opcional de solo lectura antes de aplicar — a definir si quieres que el técnico pueda corregirlo a mano antes de aplicar).
- **Botón "Aplicar diagnóstico"**: deja de leer el `content` del mensaje del bot sobre el que se hizo clic. Pasa a simplemente llamar `apply-diagnostic` sin body, habilitado solo si `draft_diagnostic` existe.
- Quitar la posibilidad actual de que el botón aparezca junto a *cualquier* burbuja de respuesta del bot; debería aparecer solo asociado al resultado de "Generar diagnóstico".

## Preguntas abiertas antes de implementar
1. Gating de estado (A o B arriba).
RESPUESTA: OPCION B
2. ¿El técnico puede **editar** el `draft_diagnostic` antes de aplicarlo, o se aplica tal cual lo generó Ohm?
RESPUESTA: QUE LO PUEDA EDITAR
3. ¿Se debe permitir **regenerar** (sobrescribir `draft_diagnostic`) si el técnico no quedó conforme, o es de una sola vez por ticket?
QUE SEA UNA SOLA VEZ
## Tests a cubrir (siguiendo tu patrón pytest/Vitest)
- Backend: generar diagnóstico con historial vacío (debe fallar o dar mensaje genérico), aplicar sin `draft_diagnostic` previo (400), aislamiento multi-tenant en el nuevo endpoint, aplicar copia exactamente el draft.
- Frontend: botón "Aplicar" deshabilitado sin draft, flujo generar → revisar → aplicar en `TechnicianWorkModal.test.jsx` o equivalente.
