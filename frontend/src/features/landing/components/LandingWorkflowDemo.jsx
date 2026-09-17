import { useState, useRef, useCallback } from "react";
import { useScrollProgress } from "../hooks/useLandingScroll";

export default function LandingWorkflowDemo() {
  const [activeStep, setActiveStep] = useState(0);
  const trackRef = useRef(null);
  const isManualClickRef = useRef(false);
  const manualTimeoutRef = useRef(null);

  const handleProgress = useCallback((p) => {
    if (isManualClickRef.current) return;
    if (typeof window !== "undefined" && window.innerWidth >= 900) {
      let nextStep = 0;
      if (p >= 0.75) nextStep = 3;
      else if (p >= 0.50) nextStep = 2;
      else if (p >= 0.25) nextStep = 1;
      else nextStep = 0;
      setActiveStep(nextStep);
    }
  }, []);

  const progress = useScrollProgress(trackRef, {
    stickyOffset: 88,
    onProgress: handleProgress,
  });

  const handleStepSelect = (idx) => {
    setActiveStep(idx);

    if (typeof window !== "undefined" && window.innerWidth >= 900 && trackRef.current) {
      isManualClickRef.current = true;
      if (manualTimeoutRef.current) clearTimeout(manualTimeoutRef.current);
      manualTimeoutRef.current = setTimeout(() => {
        isManualClickRef.current = false;
      }, 700);

      const rect = trackRef.current.getBoundingClientRect();
      const trackTop = rect.top + window.scrollY;
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
      const scrollableDistance = rect.height - (viewportHeight - 88);

      if (scrollableDistance > 0) {
        const targetRatios = [0.05, 0.35, 0.65, 0.95];
        const prefersReduced = typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const targetY = trackTop - 88 + (targetRatios[idx] * scrollableDistance);
        window.scrollTo({ top: targetY, behavior: prefersReduced ? "auto" : "smooth" });
      }
    }
  };

  const steps = [
    {
      id: "recibido",
      num: "01",
      name: "RECIBIDO",
      label: "Ingreso & Recepción",
      badgeColor: "var(--accent-glow-18)",
      badgeTextColor: "var(--color-accent)",
      summary: "Ingreso inmediato en menos de 30 segundos con comprobante y custodia de datos.",
      insightIcon: "🛡️",
      insightPill: "RECEPCIÓN & SEGURIDAD",
      insightTitle: "Custodia blindada desde el segundo cero",
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        client: "Esteban R. (Guayaquil)",
        intakeDate: "Hoy, 10:15 AM",
        status: "RECIBIDO",
        statusClass: "status-recibido",
        declaredIssue: "No da imagen tras apagón eléctrico. Enciende teclado pero pantalla en negro.",
        security: "PIN de usuario cifrado con Fernet [ •••• ]",
        evidence: "Fotografías de recepción archivadas como constancia de ingreso",
        actionNote: "Comprobante digital enviado al cliente con token de tracking directo y PIN cifrado en base de datos."
      }
    },
    {
      id: "diagnostico",
      num: "02",
      name: "EN DIAGNÓSTICO",
      label: "Banco & Medición",
      badgeColor: "var(--warning-bg)",
      badgeTextColor: "var(--color-warning)",
      summary: "Evaluación en mesón de trabajo con semáforo SLA activo y apoyo de Ohm.",
      insightIcon: "⚡",
      insightPill: "BANCO & ASISTENCIA OHM",
      insightTitle: "Resolución guiada con historial del taller",
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        assignedTech: "Christian A. (Mesón 2 - Microelectrónica)",
        slaStatus: "SLA de Taller: 3h 20m restantes para diagnóstico prometido",
        status: "EN DIAGNÓSTICO",
        statusClass: "status-diagnostico",
        findings: "Línea +VCC_EDP en 0.2V. Corto en condensador cerámico de desacople en circuito backlight.",
        ohmHelper: "Coincidencia técnica con caso #TK-7820 en placa GA401: fuga en condensador de línea backlight.",
        evidence: "Foto térmica de banco adjunta con punto caliente a 78°C en zona display.",
        actionNote: "Técnico diagnostica con apoyo del historial técnico previo del taller y semáforo de tiempo visible."
      }
    },
    {
      id: "aprobacion",
      num: "03",
      name: "APROBACIÓN",
      label: "Portal del Cliente",
      badgeColor: "var(--approval-bg)",
      badgeTextColor: "var(--approval-text)",
      summary: "El cliente revisa fotos, diagnóstico y autoriza formalmente con un clic.",
      insightIcon: "📱",
      insightPill: "APROBACIÓN DIGITAL",
      insightTitle: "Cero llamadas repetitivas o vistos sin respuesta",
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        portalUrl: "tecnidesk.app/tracking/guayaquil-zeph-9104",
        status: "PRESUPUESTO APROBADO",
        statusClass: "status-aprobado",
        quote: {
          parts: "1x Condensador cerámico SMD 0805 10uF 25V ($4.50)",
          labor: "Mano de obra especializada microelectrónica ($45.00)",
          total: "$49.50"
        },
        clientAction: "Cliente aprobó el presupuesto desde su celular hoy a las 11:42 AM.",
        whatsappNotice: "Aviso automático enviado al taller con presupuesto autorizado para proceder.",
        actionNote: "El cliente revisa fotografías y desglose formal de repuestos y mano de obra desde su navegador móvil."
      }
    },
    {
      id: "listo",
      num: "04",
      name: "LISTO / ENTREGADO",
      label: "Cierre & Garantía",
      badgeColor: "var(--success-bg)",
      badgeTextColor: "var(--color-success)",
      summary: "Reparación concluida, control de calidad verificado y garantía registrada.",
      insightIcon: "✅",
      insightPill: "TRAZABILIDAD & ENTREGA",
      insightTitle: "Historial técnico capitalizado para siempre",
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        completedBy: "Christian A. — Prueba de estrés superada (45 min FurMark OK)",
        status: "LISTO PARA ENTREGA",
        statusClass: "status-listo",
        warranty: "90 días de garantía registrada en sistema con comprobante de entrega",
        deliveryPhotos: "Foto de equipo encendido con pantalla activa archivada en el ticket",
        inventoryDeduction: "Repuesto enlazado al ticket con costo y trazabilidad de inventario",
        actionNote: "Equipo verificado con prueba de estrés, comprobante de garantía formal y stock enlazado."
      }
    }
  ];

  const current = steps[activeStep];

  return (
    <section id="workbench" className="landing-section landing-tech-zone">
      <div className="landing-container">
        <div className="landing-section-header">
          <div className="landing-badge">Demostración del Producto</div>
          <h2 className="landing-title">
            Así se vive un ticket en el Workbench de TecniDesk
          </h2>
          <p className="landing-desc">
            Seguí el ciclo de vida de una reparación real. Desde el ingreso hasta la entrega, cada etapa está conectada con el técnico, el inventario y el cliente.
          </p>
        </div>

        {/* Track Container with Calibrated Height for Scroll-Driven Experience */}
        <div ref={trackRef} className="landing-workflow-track">
          <div className="landing-workflow-sticky-window">
            {/* Stepper Navigation */}
            <div className="landing-workflow-stepper" role="tablist" aria-label="Etapas del flujo de trabajo">
              {steps.map((step, idx) => {
                const isActive = activeStep === idx;
                return (
                  <button
                    key={step.id}
                    role="tab"
                    aria-selected={isActive}
                    aria-controls={`step-panel-${step.id}`}
                    id={`step-tab-${step.id}`}
                    onClick={() => handleStepSelect(idx)}
                    className={`landing-workflow-tab ${isActive ? "active" : ""}`}
                  >
                    <span className="landing-workflow-tab-num">{step.num}</span>
                    <div className="landing-workflow-tab-text">
                      <span className="landing-workflow-tab-name">{step.name}</span>
                      <span className="landing-workflow-tab-label">{step.label}</span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Subtle Progress Bar */}
            <div className="landing-workflow-progress-bar-wrap" aria-hidden="true">
              <div
                className="landing-workflow-progress-bar-fill"
                style={{ width: `${Math.round(progress * 100)}%` }}
              />
            </div>

        {/* Interactive Step Display Panel */}
        <div
          id={`step-panel-${current.id}`}
          role="tabpanel"
          aria-labelledby={`step-tab-${current.id}`}
          className="landing-workflow-display-card"
        >
          {/* Card Topbar */}
          <div className="landing-workflow-card-topbar">
            <div className="landing-workflow-card-meta">
              <span className="landing-workflow-step-badge">
                PASO {current.num} DE 04
              </span>
              <h3 className="landing-workflow-card-title">{current.summary}</h3>
            </div>
            <span
              className="landing-workflow-status-pill"
              style={{
                backgroundColor: current.badgeColor,
                color: current.badgeTextColor
              }}
            >
              ● {current.ticket.status}
            </span>
          </div>

          {/* Workbench Interface Simulation */}
          <div className="landing-workflow-content-grid">
            {/* Left: Ticket Detail Sheet */}
            <div className="landing-workflow-ticket-sheet">
              <div className="landing-workflow-sheet-header">
                <div>
                  <span className="landing-workflow-device-id">{current.ticket.id}</span>
                  <h4 className="landing-workflow-device-name">{current.ticket.device}</h4>
                </div>
                <span className="landing-workflow-demo-tag">SIMULACIÓN DEMO</span>
              </div>

              <div className="landing-workflow-sheet-rows">
                <div key={activeStep} className="landing-workflow-stage-content">
                  {activeStep === 0 && (
                    <>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Cliente:</span>
                        <span className="data-row-value">{current.ticket.client}</span>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Fecha de Ingreso:</span>
                        <span className="data-row-value">{current.ticket.intakeDate}</span>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Falla declarada:</span>
                        <span className="data-row-value">{current.ticket.declaredIssue}</span>
                      </div>
                      <div className="landing-workflow-security-card">
                        <div className="landing-workflow-security-header">
                          <span>CUSTODIA SEGURA FERNET</span>
                          <span className="landing-workflow-security-meta">FERNET-AES / DB</span>
                        </div>
                        <div className="landing-workflow-security-body">
                          {current.ticket.security}
                        </div>
                        <div className="landing-workflow-security-footer">
                          Los datos de cada taller permanecen aislados de otros talleres.
                        </div>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Evidencia de ingreso:</span>
                        <span className="data-row-value">{current.ticket.evidence}</span>
                      </div>
                    </>
                  )}

                  {activeStep === 1 && (
                    <>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Técnico asignado:</span>
                        <span className="data-row-value">{current.ticket.assignedTech}</span>
                      </div>
                      <div className="landing-workflow-sla-card">
                        <div className="landing-workflow-sla-header">
                          <span>CONTROL DE TIEMPO / SLA</span>
                          <span className="landing-workflow-sla-meta">OBJETIVO: 4H</span>
                        </div>
                        <div className="landing-workflow-sla-body">
                          {current.ticket.slaStatus}
                        </div>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Diagnóstico de banco:</span>
                        <span className="data-row-value">{current.ticket.findings}</span>
                      </div>
                      <div className="landing-workflow-ohm-card">
                        <div className="landing-workflow-ohm-header">
                          <span>ASISTENCIA OHM</span>
                          <span className="landing-workflow-ohm-tag">HISTORIAL DEL TALLER</span>
                        </div>
                        <div className="landing-workflow-ohm-body">
                          {current.ticket.ohmHelper}
                        </div>
                        <div className="landing-workflow-ohm-footer">
                          Ohm utiliza el historial disponible del propio taller para sus consultas.
                        </div>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Evidencias:</span>
                        <span className="data-row-value">{current.ticket.evidence}</span>
                      </div>
                    </>
                  )}

                  {activeStep === 2 && (
                    <>
                      <div className="landing-workflow-data-row highlight-portal">
                        <span className="data-row-label">Portal de seguimiento:</span>
                        <span className="data-row-value code">{current.ticket.portalUrl}</span>
                      </div>
                      <div className="landing-workflow-quote-box">
                        <div className="quote-item">
                          <span>Repuesto:</span>
                          <strong>{current.ticket.quote.parts}</strong>
                        </div>
                        <div className="quote-item">
                          <span>Servicio:</span>
                          <strong>{current.ticket.quote.labor}</strong>
                        </div>
                        <div className="quote-total">
                          <span>Total Presupuesto:</span>
                          <strong>{current.ticket.quote.total}</strong>
                        </div>
                      </div>
                      <div className="landing-workflow-data-row highlight-success">
                        <span className="data-row-label">Estado de aprobación:</span>
                        <span className="data-row-value">{current.ticket.clientAction}</span>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Canal de confirmación:</span>
                        <span className="data-row-value">{current.ticket.whatsappNotice}</span>
                      </div>
                    </>
                  )}

                  {activeStep === 3 && (
                    <>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Finalización:</span>
                        <span className="data-row-value">{current.ticket.completedBy}</span>
                      </div>
                      <div className="landing-workflow-data-row highlight-success">
                        <span className="data-row-label">Garantía de servicio:</span>
                        <span className="data-row-value">{current.ticket.warranty}</span>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Inventario:</span>
                        <span className="data-row-value">{current.ticket.inventoryDeduction}</span>
                      </div>
                      <div className="landing-workflow-data-row">
                        <span className="data-row-label">Control de calidad:</span>
                        <span className="data-row-value">{current.ticket.deliveryPhotos}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Operational Benefit of this Step */}
            <div className="landing-workflow-insight-box">
              <div className="landing-workflow-insight-header">
                <span className="landing-workflow-insight-icon" role="img" aria-hidden="true">
                  {current.insightIcon}
                </span>
                <div>
                  <span className="landing-workflow-insight-pill">{current.insightPill}</span>
                  <h5>{current.insightTitle}</h5>
                </div>
              </div>
              <p className="landing-workflow-insight-text">
                {current.ticket.actionNote}
              </p>

              <div className="landing-workflow-interactive-nav">
                <button
                  type="button"
                  disabled={activeStep === 0}
                  onClick={() => handleStepSelect(Math.max(0, activeStep - 1))}
                  className="landing-btn landing-btn-secondary landing-btn-sm"
                >
                  ← Paso anterior
                </button>
                <button
                  type="button"
                  disabled={activeStep === steps.length - 1}
                  onClick={() => handleStepSelect(Math.min(steps.length - 1, activeStep + 1))}
                  className="landing-btn landing-btn-primary landing-btn-sm"
                >
                  Siguiente etapa →
                </button>
              </div>

              <div className="landing-workflow-footnote">
                Demostración con datos ficticios. En tu taller, el Workbench se sincroniza con tus propios técnicos y repuestos.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

        {/* Post-Workflow Subtle Continuity Strip */}
        <div className="landing-workflow-continuity-strip">
          <span>¿Querés probar este flujo de trabajo en tu propio mesón?</span>
          <a href="#postular" className="landing-workflow-continuity-link">
            Postular mi taller al piloto pionero →
          </a>
        </div>
      </div>
    </section>
  );
}
