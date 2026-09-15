import { useState } from "react";

export default function LandingWorkflowDemo() {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    {
      id: "recibido",
      num: "01",
      name: "RECIBIDO",
      label: "Ingreso & Recepción",
      badgeColor: "var(--accent-glow-18)",
      badgeTextColor: "var(--color-accent)",
      summary: "Ingreso inmediato en menos de 30 segundos con comprobante y custodia de datos.",
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        client: "Esteban R. (Guayaquil)",
        intakeDate: "Hoy, 10:15 AM",
        status: "RECIBIDO",
        statusClass: "status-recibido",
        declaredIssue: "No da imagen tras apagón eléctrico. Enciende teclado pero pantalla en negro.",
        security: "PIN de usuario cifrado con Fernet [ •••• ]",
        evidence: "3 fotografías de recepción registradas (sin rayones previos en chasis)",
        actionNote: "Comprobante digital enviado al cliente con token de tracking directo."
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
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        assignedTech: "Christian A. (Mesón 2 - Microelectrónica)",
        slaStatus: "SLA: 3h 20m restantes para diagnóstico prometido",
        status: "EN DIAGNÓSTICO",
        statusClass: "status-diagnostico",
        findings: "Línea +VCC_EDP en 0.2V. Corto en condensador cerámico de desacople en circuito backlight.",
        ohmHelper: "Ohm consultó historial: coincidencia con caso #TK-7820 en placa GA401.",
        evidence: "Foto térmica de banco adjunta con punto caliente a 78°C en zona display.",
        actionNote: "Técnico genera presupuesto y reserva la pieza en el inventario local."
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
        whatsappNotice: "Notificación automática al taller: «Presupuesto confirmado, podés avanzar».",
        actionNote: "Sin llamadas repetitivas ni mensajes que quedan en visto."
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
      ticket: {
        id: "#TK-9104",
        device: "Laptop ASUS ROG Zephyrus G14",
        completedBy: "Christian A. — Prueba de estrés superada (45 min FurMark OK)",
        status: "LISTO PARA ENTREGA",
        statusClass: "status-listo",
        warranty: "90 días de garantía registrada en sistema con firma de entrega",
        deliveryPhotos: "Foto de equipo encendido con pantalla activa archivada en el ticket",
        inventoryDeduction: "Pieza descontada automáticamente del stock del taller",
        actionNote: "El caso alimenta la memoria técnica de Ohm para futuras fallas similares."
      }
    }
  ];

  const current = steps[activeStep];

  return (
    <section id="workbench" className="landing-section">
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
                onClick={() => setActiveStep(idx)}
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
                    <div className="landing-workflow-data-row highlight-security">
                      <span className="data-row-label">Seguridad PIN:</span>
                      <span className="data-row-value">{current.ticket.security}</span>
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
                    <div className="landing-workflow-data-row highlight-sla">
                      <span className="data-row-label">SLA de Taller:</span>
                      <span className="data-row-value">{current.ticket.slaStatus}</span>
                    </div>
                    <div className="landing-workflow-data-row">
                      <span className="data-row-label">Diagnóstico de banco:</span>
                      <span className="data-row-value">{current.ticket.findings}</span>
                    </div>
                    <div className="landing-workflow-data-row highlight-ohm">
                      <span className="data-row-label">Memoria Ohm:</span>
                      <span className="data-row-value">{current.ticket.ohmHelper}</span>
                    </div>
                    <div className="landing-workflow-data-row">
                      <span className="data-row-label">Evidencias:</span>
                      <span className="data-row-value">{current.ticket.evidence}</span>
                    </div>
                  </>
                )}

                {activeStep === 2 && (
                  <>
                    <div className="landing-workflow-data-row">
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
                      <span className="data-row-label">Aviso WhatsApp:</span>
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

            {/* Right: Operational Benefit of this Step */}
            <div className="landing-workflow-insight-box">
              <div className="landing-workflow-insight-header">
                <span className="landing-workflow-insight-icon">💡</span>
                <h5>El valor para tu taller en esta etapa</h5>
              </div>
              <p className="landing-workflow-insight-text">
                {current.ticket.actionNote}
              </p>

              <div className="landing-workflow-interactive-nav">
                <button
                  type="button"
                  disabled={activeStep === 0}
                  onClick={() => setActiveStep((prev) => Math.max(0, prev - 1))}
                  className="landing-btn landing-btn-secondary landing-btn-sm"
                >
                  ← Paso anterior
                </button>
                <button
                  type="button"
                  disabled={activeStep === steps.length - 1}
                  onClick={() => setActiveStep((prev) => Math.min(steps.length - 1, prev + 1))}
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
