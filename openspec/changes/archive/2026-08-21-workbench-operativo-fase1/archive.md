# SDD Archive: Workbench Operativo Mínimo (Fase 1)

**Date Archived**: 2026-08-21  
**Lineage/Change Name**: `2026-08-21-workbench-operativo-fase1`  
**Status**: `archived`

## 1. Archival Manifest & Artifacts

- **[verify.md](verify.md)**: Alcance implementado verificado (24/24 escenarios), pruebas del backend (`pytest` 26/26) y build del frontend (0 errores, 1.93s).
- **[telemetry_baseline.md](telemetry_baseline.md)**: Línea base de métricas pre-lanzamiento. Captura realizada el 21/08/2026. (62 tickets totales, 62 vencidos, 49 sin técnico asignado).
- **Evidencia del orden de tickets críticos**: Modificación exitosa del `stmt.order_by` en `ticket_service.py` (`technician_id IS NULL` primero, `created_at > 72h` segundo, cronológico tercero).
- **Código y Tests**: Implementados y comiteados bajo los flujos de la Fase 1.

## 2. Decisiones Documentadas

- **Kanban como Hipótesis (Fase 3)**: Se decidió explícitamente que la vista Kanban permanece como una hipótesis a validar en la Fase 3, *no* como una implementación comprometida actual. El foco central de esta primera fase fue limpiar el flujo de trabajo (Workbench) y establecer señales operativas directas antes de mover las tarjetas visualmente.

## 3. Backlog para Fase 2 (Deuda y Refinamiento)

Las siguientes observaciones se transfieren como requerimientos normativos para la **Fase 2**:

1. **Reglas de SLA por estado (Vencimiento dinámico)**: 
   - El concepto de "Vencido" no debe ser un estático `created_at > 72h`. Equipos esperando repuestos o aprobación del cliente pueden exceder este tiempo sin ser culpa del taller. 
   - Se debe implementar SLA dinámico calculando el tiempo respecto a `last_status_changed_at` (o su equivalente del historial de transiciones) según el estado en el que se encuentre el equipo.
2. **Historial de transiciones**:
   - Requerido para dar soporte al cálculo dinámico del SLA y observar cuellos de botella (ej. cuánto tiempo pasa un ticket en `EN_ESPERA_INGRESO` vs `EN_REPARACION`).
3. **Técnico Obligatorio**:
   - Eliminar de raíz el problema de "equipos huérfanos" requiriendo siempre un técnico responsable o pasando a un estado transicional estricto.
4. **Tests de Combinatoria de Ordenamiento**:
   - Ampliar la suite de `pytest` (que hoy tiene 26 tests globales) con un módulo dedicado exclusivamente a la semántica de prioridad en `ticket_service.list_tickets()`. 
   - Crear fixtures explícitos comprobando: `Sin técnico + Vencido`, `Con técnico + Vencido`, `Sin técnico + No vencido`, y el desempate natural por antigüedad.
