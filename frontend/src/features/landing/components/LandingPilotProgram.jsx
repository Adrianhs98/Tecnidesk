export default function LandingPilotProgram() {
  return (
    <section id="piloto" className="landing-section">
      <div className="landing-container">
        <div className="landing-section-header">
          <div className="landing-badge">Alianza Pionera</div>
          <h2 className="landing-title">
            Estructura del Programa Piloto
          </h2>
          <p className="landing-desc">
            Buscamos una relación cercana con talleres que quieran profesionalizar su operación y marcar el rumbo del software. Las condiciones son exclusivas para los primeros seleccionados.
          </p>
        </div>

        <div className="landing-pilot-grid">
          {/* Card 1: Mes 1 */}
          <div className="landing-pilot-card featured">
            <div className="landing-pilot-tag">Fase de Lanzamiento</div>
            <div className="landing-pilot-period">Mes 1</div>
            <div className="landing-pilot-price">
              $0 <span>/ mes</span>
            </div>
            <p className="landing-pilot-desc">
              100% bonificado para los talleres seleccionados. Onboarding guiado e integración de tus datos iniciales.
            </p>

            <ul className="landing-pilot-features">
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Configuración de técnicos e inventario</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Acceso completo sin límites al Workbench</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Copiloto Ohm con memoria RAG activa</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Acompañamiento directo en Guayaquil / Santa Elena</span>
              </li>
            </ul>
          </div>

          {/* Card 2: Meses 2 y 3 */}
          <div className="landing-pilot-card">
            <div className="landing-pilot-period">Meses 2 y 3</div>
            <div className="landing-pilot-price">
              50% <span>de descuento</span>
            </div>
            <p className="landing-pilot-desc">
              Consolidación del sistema en el taller. Ajustes de tiempos de ciclo y soporte de alta prioridad.
            </p>

            <ul className="landing-pilot-features">
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Tarifa preferencial reducida al 50%</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Canal directo con ingenieros de producto</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Ajuste personalizado de umbrales SLA</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Reporte de métricas de rentabilidad</span>
              </li>
            </ul>
          </div>

          {/* Card 3: Mes 4+ */}
          <div className="landing-pilot-card">
            <div className="landing-pilot-period">Mes 4 en adelante</div>
            <div className="landing-pilot-price">
              Precio <span>Congelado</span>
            </div>
            <p className="landing-pilot-desc">
              Tarifa estándar mensual pero con garantía vitalicia de precio fundador para los talleres del piloto.
            </p>

            <ul className="landing-pilot-features">
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Precio preferencial fundador garantizado</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Sin contratos forzosos ni penalidades</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Acceso anticipado a nuevos módulos</span>
              </li>
              <li className="landing-pilot-feature-item">
                <span style={{ color: "var(--color-success)" }}>✓</span>
                <span>Insignia de Taller Fundador en portal público</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Requirements Box */}
        <div style={{
          marginTop: "3rem",
          backgroundColor: "var(--bg-paper)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          padding: "1.75rem",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "1.5rem"
        }}>
          <div>
            <h4 style={{ fontSize: "1.0625rem", fontWeight: 700, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
              ¿Qué buscamos en un taller piloto?
            </h4>
            <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
              Taller físico en Guayaquil o Península de Santa Elena, volumen semanal activo y ganas de trabajar con un sistema moderno.
            </p>
          </div>

          <a href="#postular" className="landing-btn landing-btn-outline landing-btn-sm">
            Ver Formulario de Postulación
          </a>
        </div>
      </div>
    </section>
  );
}
