export default function LandingHero() {
  return (
    <section className="landing-section landing-hero">
      <div className="landing-hero-glow" aria-hidden="true" />
      <div className="landing-container">
        <div className="landing-hero-grid">
          {/* Left Column: Value Proposition */}
          <div>
            <div className="landing-announcement">
              <span className="landing-announcement-dot" />
              <span>Convocatoria Abierta • Guayaquil y Santa Elena</span>
            </div>

            <h1 className="landing-hero-title">
              Estamos seleccionando talleres de Guayaquil y Santa Elena para la{" "}
              <span className="landing-highlight">prueba piloto</span> de TecniDesk.
            </h1>

            <p className="landing-hero-subtitle">
              El sistema operativo para talleres de reparación que erradica el caos en el banco de trabajo, protege los datos de tus clientes con PINs cifrados y automatiza el seguimiento en tiempo real.
            </p>

            <div className="landing-hero-actions">
              <a href="#postular" className="landing-btn landing-btn-primary landing-btn-lg">
                Postular mi taller al piloto
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </a>

              <a href="#solucion" className="landing-btn landing-btn-secondary landing-btn-lg">
                Ver cómo funciona
              </a>
            </div>

            <div className="landing-trust-chips">
              <div className="landing-chip-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Aislamiento multi-tenant</span>
              </div>
              <div className="landing-chip-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Alertas SLA dinámicas</span>
              </div>
              <div className="landing-chip-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Copiloto Ohm con RAG</span>
              </div>
            </div>
          </div>

          {/* Right Column: Interactive CSS Workbench Mockup */}
          <div>
            <div className="landing-mockup-card">
              <div className="landing-mockup-topbar">
                <div className="landing-mockup-dots">
                  <div className="landing-mockup-dot" />
                  <div className="landing-mockup-dot" />
                  <div className="landing-mockup-dot" />
                </div>
                <div className="landing-mockup-title">
                  tecnidesk.app/demo/workbench
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--color-accent)", fontWeight: 600 }}>
                  ● Vista previa de la interfaz
                </div>
              </div>

              <div className="landing-mockup-body">
                {/* Ticket Item 1 */}
                <div className="landing-mockup-ticket">
                  <div className="landing-mockup-ticket-header">
                    <span>Caso Demo • Laptop 15"</span>
                    <span style={{ color: "var(--color-warning)", fontWeight: 700 }}>Alerta SLA: 4h restantes</span>
                  </div>
                  <div className="landing-mockup-ticket-device">
                    Diagnóstico: Falla de backlight tras caída
                  </div>
                  <div className="landing-mockup-ticket-footer">
                    <span className="landing-mockup-badge landing-mockup-badge-revision">
                      EN REVISIÓN
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                      Flujo de banco de trabajo
                    </span>
                  </div>
                </div>

                {/* Ticket Item 2 */}
                <div className="landing-mockup-ticket">
                  <div className="landing-mockup-ticket-header">
                    <span>Caso Demo • Smartphone</span>
                    <span style={{ color: "var(--color-success)", fontWeight: 700 }}>Aprobado online por cliente</span>
                  </div>
                  <div className="landing-mockup-ticket-device">
                    Reparación: Cambio de módulo de pantalla
                  </div>
                  <div className="landing-mockup-ticket-footer">
                    <span className="landing-mockup-badge landing-mockup-badge-reparacion">
                      EN REPARACIÓN
                    </span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                      Trazabilidad de repuestos
                    </span>
                  </div>
                </div>

                {/* Micro Callout for Customer Portal */}
                <div style={{
                  backgroundColor: "var(--bg-canvas)",
                  border: "1px dashed var(--border-subtle)",
                  borderRadius: "6px",
                  padding: "0.75rem",
                  fontSize: "0.75rem",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between"
                }}>
                  <span>Portal de cliente: <strong>tracking/c7a10f...</strong></span>
                  <span style={{ color: "var(--color-accent)", fontWeight: 600 }}>WhatsApp listo</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
