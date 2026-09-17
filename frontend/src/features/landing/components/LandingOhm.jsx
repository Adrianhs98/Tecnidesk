import { useState } from "react";

const OHM_STAGES = [
  {
    id: "consulta",
    num: "01",
    tabLabel: "Consulta",
    stepName: "01 CONSULTA TÉCNICA",
    stepClass: "step-query",
    meta: "Técnico en microscopio • Caso activo",
    headline: "El técnico ingresa el problema directo en el banco",
    summary: "Se registra la placa, síntoma y comportamiento anómalo inicial sin rodeos.",
    renderContent: () => (
      <div className="landing-ohm-stage-content">
        <div className="landing-ohm-prompt-preview">
          <div className="landing-ohm-prompt-label">Registro del técnico en mesón:</div>
          <p className="landing-ohm-prompt-text">
            «MacBook Air M1 (Placa 820-02016) no enciende tras mojarse. Línea PP3V3_S2 marca 0.8V en lugar de 3.3V.»
          </p>
        </div>
        <div className="landing-ohm-callout-box">
          <div className="landing-ohm-callout-header">
            <span className="landing-ohm-callout-dot query" />
            <strong>Punto de partida en mesón</strong>
          </div>
          <p className="landing-ohm-callout-desc">
            El técnico describe los primeros síntomas y mediciones básicas. Ohm toma esta información para buscar patrones técnicos y relaciones en la memoria del taller.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: "memoria",
    num: "02",
    tabLabel: "Memoria",
    stepName: "02 MEMORIA DEL TALLER",
    stepClass: "step-history",
    meta: "Historial disponible consultado",
    headline: "Ohm encuentra coincidencias en reparaciones previas del taller",
    summary: "Recupera soluciones reales que tu equipo ya documentó y resolvió con éxito.",
    renderContent: () => (
      <div className="landing-ohm-stage-content">
        <div className="landing-ohm-matches-list">
          <div className="landing-ohm-match-card primary">
            <div className="landing-ohm-match-top">
              <span className="landing-ohm-match-id">Ticket #TK-7412</span>
              <span className="landing-ohm-match-badge match-high">91% de similitud con un caso previo del taller</span>
            </div>
            <div className="landing-ohm-match-body">
              <strong>Causa confirmada en tu taller:</strong> Corto en condensador cerámico C3104 en riel secundario tras derrame.
            </div>
            <div className="landing-ohm-match-footer">
              <span>Resolución registrada hace 3 meses en tu local</span>
            </div>
          </div>

          <div className="landing-ohm-match-card secondary">
            <div className="landing-ohm-match-top">
              <span className="landing-ohm-match-id">Ticket #TK-6201</span>
              <span className="landing-ohm-match-badge match-subtle">Coincidencia secundaria en misma placa</span>
            </div>
            <div className="landing-ohm-match-body">
              Sulfatación y corrosión en pin 4 del integrado U7700.
            </div>
          </div>
        </div>

        <div className="landing-ohm-callout-box memory">
          <p className="landing-ohm-callout-desc">
            💡 <strong>Memoria acumulativa:</strong> Tu taller no arranca desde cero en cada reparación. Lo que un técnico resolvió hace semanas está disponible para todo el equipo.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: "mediciones",
    num: "03",
    tabLabel: "Medición",
    stepName: "03 MEDICIONES / HALLAZGOS",
    stepClass: "step-findings",
    meta: "Riel PP3V3_S2 • Evidencia de banco",
    headline: "El técnico corrobora con multímetro antes de desoldar",
    summary: "Se confrontan las mediciones reales de placa con los valores esperados de referencia.",
    renderContent: () => (
      <div className="landing-ohm-stage-content">
        <div className="landing-ohm-measurement-grid">
          <div className="landing-ohm-measurement-card expected">
            <span className="measurement-label">Impedancia esperada a tierra</span>
            <span className="measurement-value">~450Ω</span>
            <span className="measurement-note">Modo diodo normal en riel PP3V3_S2</span>
          </div>
          <div className="landing-ohm-measurement-card measured">
            <span className="measurement-label">Valor medido en banco actual</span>
            <span className="measurement-value danger">12Ω</span>
            <span className="measurement-note">Corto parcial confirmado en circuito</span>
          </div>
        </div>

        <div className="landing-ohm-callout-box findings">
          <div className="landing-ohm-callout-header">
            <span className="landing-ohm-callout-dot findings" />
            <strong>Acompañamiento sin adivinanzas</strong>
          </div>
          <p className="landing-ohm-callout-desc">
            El técnico confirma el corto antes de aplicar calor o sustituir componentes al azar. Ohm asocia la medición de 12Ω directamente con el riel sospechoso.
          </p>
        </div>
      </div>
    ),
  },
  {
    id: "sugerencia",
    num: "04",
    tabLabel: "Sugerencia",
    stepName: "04 SUGERENCIA TÉCNICA",
    stepClass: "step-suggestion",
    meta: "Orientación técnica • Decisión del técnico",
    headline: "Orientación concreta de trabajo basada en casos reales",
    summary: "Pasos ordenados de verificación y capitalización permanente de la solución.",
    renderContent: () => (
      <div className="landing-ohm-stage-content">
        <div className="landing-ohm-suggestion-box">
          <div className="landing-ohm-suggestion-header">
            <span className="landing-ohm-suggestion-pill">Procedimiento sugerido por Ohm</span>
            <span className="landing-ohm-time-ref">Tiempo histórico: ~40 min</span>
          </div>
          <ol className="landing-ohm-suggestion-list">
            <li>
              <strong>Desoldar condensador C3104</strong> y verificar con multímetro si la línea recupera los 3.3V nominales.
            </li>
            <li>
              <strong>Inspeccionar pines de U7700</strong> con alcohol isopropílico al 99% bajo microscopio para descartar sulfatación residual.
            </li>
            <li>
              <strong>Verificar estabilidad:</strong> Someter la placa a prueba de encendido y comprobar temperatura de rieles.
            </li>
          </ol>
        </div>

        <div className="landing-ohm-capitalization-banner">
          <div className="landing-ohm-capitalization-icon">💾</div>
          <div className="landing-ohm-capitalization-text">
            <strong>Capitalización en la memoria del taller:</strong>
            <span>
              Al reparar el equipo, el técnico confirma la solución final y esta queda registrada permanentemente en la memoria técnica disponible del propio taller para futuras consultas.
            </span>
          </div>
        </div>
      </div>
    ),
  },
];

export default function LandingOhm() {
  const [activeStep, setActiveStep] = useState(0);

  const currentStage = OHM_STAGES[activeStep];

  const handleNext = () => {
    setActiveStep((prev) => (prev < OHM_STAGES.length - 1 ? prev + 1 : 0));
  };

  const handlePrev = () => {
    setActiveStep((prev) => (prev > 0 ? prev - 1 : 0));
  };

  return (
    <section id="ohm" className="landing-section" data-ohm-step={activeStep}>
      <div className="landing-container">
        <div className="landing-ohm-box">
          <div className="landing-ohm-glow" aria-hidden="true" />

          {/* Section Header */}
          <div className="landing-ohm-header-wrap">
            <div className="landing-badge" style={{ backgroundColor: "var(--accent-glow-28)" }}>
              Copiloto de Banco de Trabajo
            </div>
            <h2 className="landing-title">
              Tu taller empieza a recordar: memoria técnica asistida
            </h2>
            <p className="landing-desc" style={{ maxWidth: "780px", margin: "0 auto" }}>
              Ohm no es un chatbot genérico ni reemplaza al técnico. Es una herramienta de banco conectada a la memoria de tu propio taller que recuerda mediciones, componentes y soluciones que tu equipo ya resolvió con éxito.
            </p>
          </div>

          <div className="landing-ohm-grid">
            {/* Left: Key Pillars */}
            <div className="landing-ohm-pillars">
              <div className="landing-ohm-pillar-card">
                <div className="landing-ohm-pillar-num">01</div>
                <div>
                  <h4 className="landing-ohm-pillar-title">
                    Aprovecha tus soluciones previas
                  </h4>
                  <p className="landing-ohm-pillar-desc">
                    Cuando un técnico pasa 3 horas descifrando una falla compleja, esa solución queda catalogada. Si la misma falla vuelve meses después, el taller la resuelve en minutos.
                  </p>
                </div>
              </div>

              <div className="landing-ohm-pillar-card">
                <div className="landing-ohm-pillar-num">02</div>
                <div>
                  <h4 className="landing-ohm-pillar-title">
                    Aislamiento multi-tenant estricto
                  </h4>
                  <p className="landing-ohm-pillar-desc">
                    Tus diagramas, trucos de micro-soldadura, costos de piezas y notas de mesón se mantienen estrictamente aislados en tu taller.
                  </p>
                </div>
              </div>

              <div className="landing-ohm-pillar-card">
                <div className="landing-ohm-pillar-num">03</div>
                <div>
                  <h4 className="landing-ohm-pillar-title">
                    Acompañamiento sin adivinanzas
                  </h4>
                  <p className="landing-ohm-pillar-desc">
                    Ohm sugiere puntos de medición y componentes sospechosos basándose en casos reales documentados, asistiendo a técnicos junior sin sobrecargar al técnico principal.
                  </p>
                </div>
              </div>
            </div>

            {/* Right: Interactive Workshop Bench Diagnostic Station */}
            <div className="landing-ohm-bench-container">
              <div className="landing-ohm-bench-card">
                {/* Station Topbar with Status and Mode */}
                <div className="landing-ohm-bench-topbar">
                  <div className="landing-ohm-bench-title-wrap">
                    <span className="landing-ohm-bench-status-dot" />
                    <span className="landing-ohm-bench-title">Estación de Diagnóstico Ohm • Mesón Activo</span>
                  </div>
                  <span className="landing-ohm-bench-tag">Historial Local Conectado</span>
                </div>

                {/* Stepper Navigation */}
                <div
                  className="landing-ohm-stepper"
                  role="tablist"
                  aria-label="Etapas de diagnóstico de Ohm"
                >
                  {OHM_STAGES.map((stage, idx) => {
                    const isActive = activeStep === idx;
                    return (
                      <button
                        key={stage.id}
                        role="tab"
                        id={`ohm-tab-${stage.id}`}
                        aria-selected={isActive}
                        aria-controls={`ohm-panel-${stage.id}`}
                        onClick={() => setActiveStep(idx)}
                        className={`landing-ohm-tab ${isActive ? "active" : ""}`}
                      >
                        <span className="landing-ohm-tab-num">{stage.num}</span>
                        <span className="landing-ohm-tab-label">{stage.tabLabel}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Interactive Body with Stable Min-Height */}
                <div
                  id={`ohm-panel-${currentStage.id}`}
                  role="tabpanel"
                  aria-labelledby={`ohm-tab-${currentStage.id}`}
                  className="landing-ohm-bench-body"
                >
                  <div className="landing-ohm-step-block active">
                    <div className="landing-ohm-step-header">
                      <span className={`landing-ohm-step-indicator ${currentStage.stepClass}`}>
                        {currentStage.stepName}
                      </span>
                      <span className="landing-ohm-step-meta">{currentStage.meta}</span>
                    </div>

                    <div className="landing-ohm-stage-meta-row">
                      <h4 className="landing-ohm-stage-headline">{currentStage.headline}</h4>
                      <p className="landing-ohm-stage-summary">{currentStage.summary}</p>
                    </div>

                    {currentStage.renderContent()}
                  </div>

                  {/* Forward / Backward Action Bar */}
                  <div className="landing-ohm-action-bar">
                    <button
                      type="button"
                      onClick={handlePrev}
                      disabled={activeStep === 0}
                      className="landing-ohm-btn landing-ohm-btn-secondary"
                      aria-label="Etapa anterior de Ohm"
                    >
                      ← Anterior
                    </button>

                    <div className="landing-ohm-step-progress" aria-hidden="true">
                      {OHM_STAGES.map((_, i) => (
                        <span
                          key={i}
                          className={`landing-ohm-progress-dot ${i === activeStep ? "active" : ""}`}
                        />
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={handleNext}
                      className="landing-ohm-btn landing-ohm-btn-primary"
                      aria-label={activeStep === OHM_STAGES.length - 1 ? "Reiniciar recorrido de Ohm" : "Siguiente etapa de Ohm"}
                    >
                      {activeStep === OHM_STAGES.length - 1 ? "Reiniciar recorrido ↺" : "Siguiente etapa →"}
                    </button>
                  </div>
                </div>

                {/* Strictly Compliant Privacy Footer */}
                <div className="landing-ohm-bench-footer">
                  <span>🔒 Los datos de cada taller permanecen aislados de otros talleres. Ohm utiliza el historial disponible del propio taller para sus consultas.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
