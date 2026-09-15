export default function LandingOhm() {
  return (
    <section id="ohm" className="landing-section">
      <div className="landing-container">
        <div className="landing-ohm-box">
          <div className="landing-ohm-glow" aria-hidden="true" />

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

            {/* Right: Workshop Bench Diagnostic Interface Simulation */}
            <div>
              <div className="landing-ohm-bench-card">
                <div className="landing-ohm-bench-topbar">
                  <div className="landing-ohm-bench-title-wrap">
                    <span className="landing-ohm-bench-status-dot" />
                    <span className="landing-ohm-bench-title">Estación de Diagnóstico Ohm • Mesón Activo</span>
                  </div>
                  <span className="landing-ohm-bench-tag">Historial Local Conectado</span>
                </div>

                <div className="landing-ohm-bench-body">
                  {/* Step 1: Technical Query */}
                  <div className="landing-ohm-step-block">
                    <div className="landing-ohm-step-header">
                      <span className="landing-ohm-step-indicator step-query">1. CONSULTA TÉCNICA</span>
                      <span className="landing-ohm-step-meta">Técnico en microscopio</span>
                    </div>
                    <div className="landing-ohm-step-content query-text">
                      «MacBook Air M1 (Placa 820-02016) no enciende tras mojarse. Línea PP3V3_S2 marca 0.8V en lugar de 3.3V.»
                    </div>
                  </div>

                  {/* Step 2: Historical Matching */}
                  <div className="landing-ohm-step-block">
                    <div className="landing-ohm-step-header">
                      <span className="landing-ohm-step-indicator step-history">2. CASOS SIMILARES EN TU TALLER</span>
                      <span className="landing-ohm-step-meta">Base interna verificada</span>
                    </div>
                    <div className="landing-ohm-step-content history-matches">
                      <div className="history-match-item">
                        <span className="history-match-id">Ticket #TK-7412:</span>
                        <span>Corto en condensador cerámico C3104 en riel secundario.</span>
                      </div>
                      <div className="history-match-item">
                        <span className="history-match-id">Ticket #TK-6201:</span>
                        <span>Sulfatación y corrosión en pin 4 del integrado U7700.</span>
                      </div>
                    </div>
                  </div>

                  {/* Step 3: Bench Findings */}
                  <div className="landing-ohm-step-block">
                    <div className="landing-ohm-step-header">
                      <span className="landing-ohm-step-indicator step-findings">3. HALLAZGOS Y MEDICIONES</span>
                      <span className="landing-ohm-step-meta">Riel PP3V3_S2</span>
                    </div>
                    <div className="landing-ohm-step-content findings-text">
                      Impedancia típica esperada a tierra: <strong>~450Ω</strong> (modo diodo).
                      <br />
                      Valor medido en banco actual: <strong>12Ω</strong> ➔ Corto parcial confirmado en circuito.
                    </div>
                  </div>

                  {/* Step 4: Suggested Action */}
                  <div className="landing-ohm-step-block suggestion-block">
                    <div className="landing-ohm-step-header">
                      <span className="landing-ohm-step-indicator step-suggestion">4. SUGERENCIA DE DIAGNÓSTICO</span>
                      <span className="landing-ohm-step-meta">Decisión final del técnico</span>
                    </div>
                    <div className="landing-ohm-step-content suggestion-text">
                      <ol style={{ margin: 0, paddingLeft: "1.2rem", display: "flex", flexDirection: "column", gap: "0.25rem" }}>
                        <li>Desoldar condensador <strong>C3104</strong> y verificar si la línea recupera los 3.3V.</li>
                        <li>Inspeccionar pines de <strong>U7700</strong> con alcohol isopropílico al 99% bajo microscopio.</li>
                        <li>Tiempo promedio registrado en tu taller para esta reparación: <strong>~40 minutos</strong>.</li>
                      </ol>
                    </div>
                  </div>
                </div>

                <div className="landing-ohm-bench-footer">
                  <span>🔒 Datos 100% aislados por taller. Ohm aprende exclusivamente del historial de tu negocio.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
