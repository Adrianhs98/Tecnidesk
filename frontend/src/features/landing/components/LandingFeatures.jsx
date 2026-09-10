export default function LandingFeatures() {
  const features = [
    {
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="9"></rect>
          <rect x="14" y="3" width="7" height="5"></rect>
          <rect x="14" y="12" width="7" height="9"></rect>
          <rect x="3" y="16" width="7" height="5"></rect>
        </svg>
      ),
      title: "Workbench y Kanban Operativo",
      desc: "Visión panorámica de todos los equipos del taller. Filtra por técnico, marca, fecha de ingreso o nivel de urgencia sin recargar la pantalla."
    },
    {
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <polyline points="12 6 12 12 16 14"></polyline>
        </svg>
      ),
      title: "Motor de Alertas y Cumplimiento de SLA",
      desc: "Evita cuellos de botella antes de que ocurran. El sistema calcula umbrales dinámicos y marca visualmente los equipos que requieren atención prioritaria."
    },
    {
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"></path>
        </svg>
      ),
      title: "Portal de Banco de Trabajo del Técnico",
      desc: "Diseñado para el mesón de reparación. Carga evidencias fotográficas comprimidas en el navegador, registra piezas y redacta diagnósticos precisos."
    },
    {
      icon: (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
        </svg>
      ),
      title: "Portal Whitelabel para el Cliente",
      desc: "Tus clientes acceden con un token seguro para revisar el estado en vivo, ver fotos de la falla y aprobar presupuestos con enlace directo a tu WhatsApp."
    }
  ];

  return (
    <section id="workbench" className="landing-section landing-section-alt">
      <div className="landing-container">
        <div className="landing-section-header">
          <div className="landing-badge">Capacidades del Sistema</div>
          <h2 className="landing-title">
            Una plataforma completa, construida para talleres reales
          </h2>
          <p className="landing-desc">
            Cada módulo responde a una necesidad del día a día del taller: velocidad de atención, control de inventario y comunicación transparente con el usuario.
          </p>
        </div>

        <div className="landing-features-grid">
          {features.map((feat, idx) => (
            <div key={idx} className="landing-feature-card">
              <div className="landing-feature-icon">
                {feat.icon}
              </div>
              <h3 className="landing-feature-title">{feat.title}</h3>
              <p className="landing-feature-desc">{feat.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
