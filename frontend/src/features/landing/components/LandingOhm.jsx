export default function LandingOhm() {
  return (
    <section id="ohm" className="landing-section">
      <div className="landing-container">
        <div className="landing-ohm-box">
          <div className="landing-ohm-glow" aria-hidden="true" />

          <div className="landing-ohm-grid">
            {/* Left: Value Proposition */}
            <div>
              <div className="landing-badge" style={{ backgroundColor: "var(--accent-glow-28)" }}>
                Copiloto de Inteligencia Artificial
              </div>

              <h2 className="landing-title">
                Conoce a Ohm: la memoria técnica de tu taller
              </h2>

              <p className="landing-desc" style={{ marginBottom: "1.5rem" }}>
                Ohm no es un chatbot genérico que inventa respuestas. Es un motor de diagnóstico asistido por <strong>RAG (Retrieval-Augmented Generation)</strong> que cataloga y consulta el historial verificado de reparaciones de tu propio taller a medida que tu equipo trabaja.
              </p>

              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div style={{ display: "flex", gap: "0.75rem" }}>
                  <div style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    backgroundColor: "var(--accent-glow-22)",
                    color: "var(--color-accent)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    flexShrink: 0
                  }}>
                    1
                  </div>
                  <div>
                    <h4 style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--text-primary)" }}>
                      Construye la memoria técnica de tu taller
                    </h4>
                    <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                      Cada solución, medición y componente registrado en el banco de trabajo alimenta la base de conocimiento local, permitiendo reutilizar diagnósticos en casos similares.
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "0.75rem" }}>
                  <div style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    backgroundColor: "var(--accent-glow-22)",
                    color: "var(--color-accent)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    flexShrink: 0
                  }}>
                    2
                  </div>
                  <div>
                    <h4 style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--text-primary)" }}>
                      Aislamiento multi-tenant estricto
                    </h4>
                    <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                      Tus notas internas, costos de piezas y trucos de banco de trabajo jamás se comparten con otros talleres de la plataforma.
                    </p>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "0.75rem" }}>
                  <div style={{
                    width: 28,
                    height: 28,
                    borderRadius: 6,
                    backgroundColor: "var(--accent-glow-22)",
                    color: "var(--color-accent)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    flexShrink: 0
                  }}>
                    3
                  </div>
                  <div>
                    <h4 style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--text-primary)" }}>
                      Acelerador para nuevos técnicos
                    </h4>
                    <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                      Permite que técnicos junior resuelvan diagnósticos complejos apoyándose en el conocimiento institucional acumulado del negocio.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Ohm Workbench Terminal Simulation */}
            <div>
              <div className="landing-ohm-terminal">
                <div className="landing-ohm-terminal-header">
                  <span>ohm-copilot://rag-engine/v1</span>
                  <span style={{ color: "#58a6ff" }}>● RAG Conectado</span>
                </div>

                <div className="landing-ohm-terminal-prompt">
                  &gt; Consulta Técnico: "MacBook Air M1 no enciende tras mojarse con café. Línea PP3V3_S2 da 0.8V."
                </div>

                <div className="landing-ohm-terminal-rag">
                  🔍 [RAG Local]: 3 tickets similares encontrados en el historial de este taller:
                  <br />
                  • Ticket #TK-7412 (Jun 2026): Condensador C3104 en corto.
                  <br />
                  • Ticket #TK-6201 (Mar 2026): Corrosión en pin 4 del U7700.
                </div>

                <div className="landing-ohm-terminal-response">
                  💡 <strong>Diagnóstico sugerido por Ohm:</strong>
                  <br />
                  1. Medir impedancia en C3104 respecto a GND (falla frecuente por diseño en este modelo).
                  <br />
                  2. Limpieza ultrasónica en zona U7700 antes de inyectar 1.2V con cámara térmica.
                  <br />
                  3. Tiempo estimado promedio de este taller para este caso: <strong>45 min</strong>.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
