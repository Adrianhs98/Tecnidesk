export default function LandingPainRelief() {
  return (
    <section id="solucion" className="landing-section landing-section-alt">
      <div className="landing-container">
        <div className="landing-section-header">
          <div className="landing-badge">El Reto Operativo</div>
          <h2 className="landing-title">
            Tu taller pierde dinero en el desorden, no en la reparación
          </h2>
          <p className="landing-desc">
            Comparamos la fricción diaria de un taller dependiente de libretas y WhatsApp frente a la trazabilidad automatizada de TecniDesk.
          </p>
        </div>

        <div className="landing-pain-grid">
          {/* Card: Tradicional */}
          <div className="landing-pain-card pain">
            <div className="landing-pain-card-header">
              <div style={{
                width: 38,
                height: 38,
                borderRadius: 8,
                backgroundColor: "var(--error-bg)",
                color: "var(--color-danger)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.25rem"
              }}>
                ✕
              </div>
              <h3 className="landing-pain-card-title">Gestión Tradicional en Papel / Chats</h3>
            </div>

            <ul className="landing-pain-list">
              <li className="landing-pain-item">
                <span className="landing-pain-icon-fail">✕</span>
                <span>
                  <strong>Interrupciones continuas:</strong> Clientes llamando o escribiendo a toda hora: "¿Ya está listo mi equipo?".
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-fail">✕</span>
                <span>
                  <strong>Pérdida de credenciales:</strong> PINs y patrones anotados en cintas adhesivas que se borran o extravían.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-fail">✕</span>
                <span>
                  <strong>Equipos olvidados en percha:</strong> Dispositivos que pasan 10+ días sin diagnóstico por falta de control de tiempos.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-fail">✕</span>
                <span>
                  <strong>Presupuestos varados:</strong> Negociaciones que quedan en visto en WhatsApp sin confirmación vinculante.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-fail">✕</span>
                <span>
                  <strong>Conocimiento disperso:</strong> La solución que un técnico descubrió hoy no queda registrada para el resto del equipo.
                </span>
              </li>
            </ul>
          </div>

          {/* Card: Con TecniDesk */}
          <div className="landing-pain-card relief">
            <div className="landing-pain-card-header">
              <div style={{
                width: 38,
                height: 38,
                borderRadius: 8,
                backgroundColor: "var(--success-bg)",
                color: "var(--color-success)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.25rem"
              }}>
                ✓
              </div>
              <h3 className="landing-pain-card-title">Trazabilidad Total con TecniDesk</h3>
            </div>

            <ul className="landing-pain-list">
              <li className="landing-pain-item">
                <span className="landing-pain-icon-success">✓</span>
                <span>
                  <strong>Portal de Tracking Whitelabel:</strong> Tu cliente consulta el avance y aprueba presupuestos 24/7 sin interrumpir a los técnicos.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-success">✓</span>
                <span>
                  <strong>PINs con cifrado militar (Fernet):</strong> Seguridad absoluta de datos privados sin riesgo de filtración.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-success">✓</span>
                <span>
                  <strong>Semáforos de SLA activos:</strong> Badges visuales de urgencia para ingresar, revisar y reparar dentro del plazo prometido.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-success">✓</span>
                <span>
                  <strong>Aprobación formal con un clic:</strong> Notificaciones directas cuando el cliente autoriza repuestos y mano de obra.
                </span>
              </li>
              <li className="landing-pain-item">
                <span className="landing-pain-icon-success">✓</span>
                <span>
                  <strong>Memoria técnica centralizada:</strong> Todo diagnóstico, pieza y falla recurrente alimenta el banco de conocimiento del taller.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
