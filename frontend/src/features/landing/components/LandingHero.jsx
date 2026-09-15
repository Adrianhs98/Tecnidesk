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
              <span>Convocatoria Piloto 2026 • Guayaquil y Santa Elena</span>
            </div>

            <h1 className="landing-hero-title">
              El sistema operativo para tu{" "}
              <span className="landing-highlight">taller de reparación tecnológica</span>.
            </h1>

            {/* High-Hierarchy Offer Banner */}
            <div className="landing-hero-offer-card">
              <div className="landing-hero-offer-header">
                <span className="landing-hero-offer-pill">PROGRAMA PILOTO EXCLUSIVO</span>
                <span className="landing-hero-offer-city">Guayaquil • Santa Elena</span>
              </div>
              <div className="landing-hero-offer-body">
                <div className="landing-hero-offer-price-row">
                  <span className="landing-hero-offer-amount">$0</span>
                  <div className="landing-hero-offer-amount-text">
                    <strong>Primer mes 100% bonificado</strong>
                    <span>Sin contratos forzosos • Acompañamiento directo</span>
                  </div>
                </div>
                <p className="landing-hero-offer-note">
                  Vamos directamente a tu local a configurar técnicos, inventario y dejar tu mesón de trabajo operando con el sistema.
                </p>
              </div>
            </div>

            <p className="landing-hero-subtitle">
              Elimina libretas y chats desordenados. Gestiona tickets con semáforos de SLA, protege los PINs de tus clientes con cifrado Fernet y utiliza a Ohm, el copiloto que recuerda las fallas y soluciones de tu propio taller.
            </p>

            <div className="landing-hero-actions">
              <a href="#postular" className="landing-btn landing-btn-primary landing-btn-lg">
                Postular mi taller al piloto
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                  <polyline points="12 5 19 12 12 19"></polyline>
                </svg>
              </a>

              <a href="#workbench" className="landing-btn landing-btn-secondary landing-btn-lg">
                Ver demostración en vivo
              </a>
            </div>

            <div className="landing-trust-chips">
              <div className="landing-chip-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Onboarding guiado</span>
              </div>
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
                <span>Cifrado Fernet de PINs</span>
              </div>
              <div className="landing-chip-item">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Copiloto Ohm con RAG local</span>
              </div>
            </div>
          </div>

          {/* Right Column: Workbench Live Preview Card */}
          <div>
            <div className="landing-mockup-card">
              <div className="landing-mockup-topbar">
                <div className="landing-mockup-dots">
                  <div className="landing-mockup-dot" />
                  <div className="landing-mockup-dot" />
                  <div className="landing-mockup-dot" />
                </div>
                <div className="landing-mockup-title">
                  tecnidesk.app/workbench • Banco Activo
                </div>
                <div className="landing-mockup-live-status">
                  <span className="landing-pulse-indicator" />
                  <span>En vivo</span>
                </div>
              </div>

              <div className="landing-mockup-body">
                {/* Ticket Item 1: MacBook in inspection with Ohm reference */}
                <div className="landing-mockup-ticket">
                  <div className="landing-mockup-ticket-header">
                    <span className="landing-ticket-id">#TK-8041 • MacBook Air M1</span>
                    <span className="landing-ticket-sla-warn">SLA: 2h restantes</span>
                  </div>
                  <div className="landing-mockup-ticket-device">
                    Diagnóstico: Corto en línea PP3V3_S2 tras derrame de líquido
                  </div>
                  <div className="landing-mockup-ticket-meta">
                    <span className="landing-pin-tag">PIN: Cifrado Fernet [••••]</span>
                    <span className="landing-ohm-tag">Ohm: Caso similar TK-7412</span>
                  </div>
                  <div className="landing-mockup-ticket-footer">
                    <span className="landing-mockup-badge landing-mockup-badge-revision">
                      EN REVISIÓN
                    </span>
                    <span className="landing-mockup-tech">Técnico: Christian A.</span>
                  </div>
                </div>

                {/* Ticket Item 2: Smartphone approved by customer */}
                <div className="landing-mockup-ticket">
                  <div className="landing-mockup-ticket-header">
                    <span className="landing-ticket-id">#TK-8038 • Samsung Galaxy S23</span>
                    <span className="landing-ticket-approved">✓ Aprobado por cliente</span>
                  </div>
                  <div className="landing-mockup-ticket-device">
                    Reparación: Cambio de módulo de pantalla + sellado IP68
                  </div>
                  <div className="landing-mockup-ticket-meta">
                    <span className="landing-quote-tag">Presupuesto: $135.00</span>
                    <span className="landing-parts-tag">Repuesto reservado en stock</span>
                  </div>
                  <div className="landing-mockup-ticket-footer">
                    <span className="landing-mockup-badge landing-mockup-badge-reparacion">
                      EN REPARACIÓN
                    </span>
                    <span className="landing-mockup-tech">Técnico: Roberto M.</span>
                  </div>
                </div>

                {/* Customer Portal Link Callout */}
                <div className="landing-mockup-portal-callout">
                  <div>
                    <span className="landing-portal-label">Portal de seguimiento del cliente:</span>
                    <div className="landing-portal-url">tecnidesk.app/tracking/allvitech-8f2e</div>
                  </div>
                  <span className="landing-portal-badge">WhatsApp Listo</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
