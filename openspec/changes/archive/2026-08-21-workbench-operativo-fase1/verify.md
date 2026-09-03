# Verification Report: Workbench Operativo Mínimo (Fase 1)

**Change**: `2026-08-21-workbench-operativo-fase1`  
**Status**: verified ✅  
**Date**: 2026-08-21  
**Spec Reference**: [`specs/workbench/spec.md`](specs/workbench/spec.md)  
**Tasks Reference**: [`tasks.md`](tasks.md)  

---

## 1. Specification Coverage Matrix (24/24 Scenarios)

| Feature | Scenario | Result | Evidence |
|---|---|:---:|---|
| **workbench-card-declutter** | Scenario 1: Essential surface | PASS | `AdminTicketCard.test.jsx` ("Surface Declutter & Operational Signals") |
| | Scenario 2: Detail modal open | PASS | `AdminTicketCard.test.jsx` ("Detail Modal Deep Inspection") |
| | Scenario 3: PII toggle | PASS | `AdminTicketCard.test.jsx` ("toggles PII visibility in the modal") |
| **workbench-kpi-filters** | Scenario 4: Click En taller | PASS | `AdminDashboard.test.jsx` ("filters by 'activos'") |
| | Scenario 5: Click Listos | PASS | `AdminDashboard.test.jsx` ("filters by 'listos'") |
| | Scenario 6: Click En espera | PASS | `AdminDashboard.test.jsx` ("filters by 'espera'") |
| | Scenario 7: KPI toggle off | PASS | `AdminDashboard.test.jsx` ("clears KPI filter when clicking the already active KPI card") |
| **workbench-exception-badges** | Scenario 8: Sin técnico badge | PASS | `AdminTicketCard.test.jsx` ("displays 'Sin técnico' badge") |
| | Scenario 9: Sin diagnóstico badge | PASS | `AdminTicketCard.test.jsx` ("displays 'Sin diagnóstico' badge") |
| | Scenario 10: Vencido badge (>72h) | PASS | `AdminTicketCard.test.jsx` ("displays 'Vencido' badge") |
| | Scenario 11: Listo p/ retiro badge | PASS | `AdminTicketCard.test.jsx` ("displays 'Listo p/ retiro' badge") |
| | Scenario 12: Esperando aprobación badge | PASS | `AdminTicketCard.test.jsx` ("displays 'Esperando aprobación' badge") |
| | Scenario 13: Clean ticket with no badges | PASS | `AdminTicketCard.test.jsx` ("displays no exception badges on healthy ticket") |
| **workbench-smart-actions** | Scenario 14: Priority 1 - Asignar | PASS | `AdminTicketCard.test.jsx` ("priority 1: shows 'Asignar' button") |
| | Scenario 15: Priority 2 - Diagnosticar | PASS | `AdminTicketCard.test.jsx` ("priority 2: shows 'Diagnosticar' button") |
| | Scenario 16: Priority 3 - WhatsApp Retiro | PASS | `AdminTicketCard.test.jsx` ("priority 3: shows 'WhatsApp: Retiro' link") |
| | Scenario 17: Priority 4 - WhatsApp Seguimiento | PASS | `AdminTicketCard.test.jsx` ("priority 4: shows 'WhatsApp: Seguimiento' link") |
| | Scenario 18: Default - Ver detalle | PASS | `AdminTicketCard.test.jsx` ("default: shows 'Ver detalle' button") |
| **workbench-network-optimization** | Scenario 19: No evidences on mount | PASS | `AdminTicketCard.test.jsx` ("does NOT fetch evidences on mount") |
| | Scenario 20: Evidences loaded on modal open | PASS | `AdminTicketCard.test.jsx` ("fetches evidences when modal is open") |
| **Backend filter_group** | Scenario 21: `filter_group=activos` | PASS | `test_ticket_filter_group.py` & `test_tickets.py` |
| | Scenario 22: Precedence of `ticket_status` | PASS | `test_ticket_filter_group.py` |
| **Date utilities** | Scenario 23: `formatRelativeAge` | PASS | `date.test.js` (7 test cases) |
| | Scenario 24: `isTicketStale` (>72h) | PASS | `date.test.js` (6 test cases) |

---

## 2. Test Execution Summary

### Backend Tests (`pytest`)
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\cntmi\Desktop\Tecnidesk\backend
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.13.0, asyncio-1.4.0, respx-0.23.1
asyncio: mode=Mode.AUTO
collected 26 items

tests\integration\test_main.py .                                         [  3%]
tests\integration\test_tickets.py .                                      [  7%]
tests\unit\test_activate_shop_guard.py .....                             [ 26%]
tests\unit\test_auth_schemas.py ...                                      [ 38%]
tests\unit\test_diagnostic_services.py ......                            [ 61%]
tests\unit\test_example.py .                                             [ 65%]
tests\unit\test_health.py .                                              [ 69%]
tests\unit\test_rejection_reason.py ..                                   [ 76%]
tests\unit\test_ticket_filter_group.py .                                 [ 80%]
tests\unit\test_tracking_validation.py ...                               [ 92%]
tests\unit\test_whatsapp_sanitization.py ..                              [100%]

======================= 26 passed, 1 warning in 14.80s ========================
```

### Frontend Tests (`vitest`)
```
 RUN  v3.2.7 C:/Users/cntmi/Desktop/Tecnidesk/frontend

 ✓ src/tests/utils/currency.test.ts (7 tests) 2ms
 ✓ src/tests/utils/date.test.js (13 tests) 7ms
 ✓ src/tests/components/Example.test.tsx (1 test) 19ms
 ✓ src/tests/components/AdminTicketCard.test.jsx (16 tests) 234ms
 ✓ src/tests/features/AdminDashboard.test.jsx (6 tests) 301ms

 Test Files  5 passed (5)
      Tests  43 passed (43)
```

### Frontend Production Build (`npm run build`)
```
✓ 1866 modules transformed.
rendering chunks...
dist/index.html                               0.47 kB │ gzip:  0.30 kB
dist/assets/index-BzoiYwSI.css               32.65 kB │ gzip:  7.27 kB
dist/assets/AdminDashboard-DnvY4BhS.js       99.01 kB │ gzip: 35.02 kB
dist/assets/index-BjO6Ag3b.js               259.15 kB │ gzip: 82.33 kB
✓ built in 1.93s
```
