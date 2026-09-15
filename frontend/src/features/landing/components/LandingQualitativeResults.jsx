export default function LandingQualitativeResults() {
  const qualitativeBenefits = [
    {
      icon: "🔬",
      title: "Menos interrupciones en el banco",
      desc: "El cliente revisa el avance desde su propio enlace de tracking. El técnico puede concentrarse en el microscopio sin contestar llamadas constantes preguntando si ya quedó listo."
    },
    {
      icon: "📸",
      title: "Evidencias visuales contra reclamos",
      desc: "Fotografías de ingreso de chasis, pantalla y sellos de garantía archivadas en el ticket. Si surge una duda sobre el estado estético previo, hay respaldo fotográfico inmediato."
    },
    {
      icon: "📋",
      title: "Presupuestos claros y aprobados",
      desc: "Desglose formal de repuestos requeridos y mano de obra con autorización digital vinculante. Evita malentendidos sobre qué piezas o costos aceptó el cliente."
    },
    {
      icon: "🔐",
      title: "Custodia de datos y PINs cifrados",
      desc: "Contraseñas y patrones de desbloqueo protegidos con cifrado Fernet. El técnico accede a la clave solo al momento de realizar pruebas de control de calidad."
    },
    {
      icon: "🧠",
      title: "Memoria técnica que se queda en el taller",
      desc: "El diagnóstico de una falla difícil queda guardado. Si entra un caso idéntico semanas después, cualquier técnico de tu equipo puede consultar la solución previa."
    },
    {
      icon: "📦",
      title: "Trazabilidad de repuestos por equipo",
      desc: "Sabes exactamente qué pantalla, batería o circuito integrado se colocó en cada equipo, asociándolo a su costo real de inventario sin pérdidas invisibles."
    }
  ];

  const onboardingSteps = [
    {
      step: "1",
      title: "Puesta en marcha en tu propio taller",
      desc: "En Guayaquil y Santa Elena coordinamos una visita directa a tu local para dejar configurados los perfiles de técnicos, mesones y accesos."
    },
    {
      step: "2",
      title: "Carga de datos y repuestos iniciales",
      desc: "Te acompañamos a ingresar tus piezas más recurrentes para que el sistema empiece a operar con tu inventario real desde el primer día."
    },
    {
      step: "3",
      title: "Soporte directo vía WhatsApp",
      desc: "Canal prioritario con nosotros durante toda la prueba piloto para resolver cualquier duda operativa mientras tu equipo atiende clientes."
    },
    {
      step: "4",
      title: "Privacidad y aislamiento garantizado",
      desc: "Tus clientes, costos y notas técnicas residen en un entorno multi-tenant, estrictamente aislados en tu taller."
    }
  ];

  return (
    <section id="beneficios" className="landing-section landing-section-alt">
      <div className="landing-container">
        {/* Section Header */}
        <div className="landing-section-header">
          <div className="landing-badge">Impacto Operativo</div>
          <h2 className="landing-title">
            Tranquilidad y orden para vos y tu equipo de trabajo
          </h2>
          <p className="landing-desc">
            TecniDesk no es una planilla de cálculo maquillada: es un flujo de trabajo construido para proteger tu tiempo, tus técnicos y la relación con tus clientes.
          </p>
        </div>

        {/* Qualitative Benefits Grid */}
        <div className="landing-qualitative-grid">
          {qualitativeBenefits.map((benefit, idx) => (
            <div key={idx} className="landing-qualitative-card">
              <div className="landing-qualitative-icon">{benefit.icon}</div>
              <h3 className="landing-qualitative-title">{benefit.title}</h3>
              <p className="landing-qualitative-desc">{benefit.desc}</p>
            </div>
          ))}
        </div>

        {/* Confidence & Accompaniment Block */}
        <div className="landing-onboarding-card">
          <div className="landing-onboarding-header">
            <div>
              <span className="landing-onboarding-pill">Acompañamiento Real</span>
              <h3 className="landing-onboarding-title">
                ¿Cómo te ayudamos a ponerlo a funcionar?
              </h3>
            </div>
            <p className="landing-onboarding-subtitle">
              No te entregamos un usuario para que te las arregles solo. Te acompañamos a implementarlo en tu taller para que el cambio no interrumpa tu operación.
            </p>
          </div>

          <div className="landing-onboarding-grid">
            {onboardingSteps.map((item, idx) => (
              <div key={idx} className="landing-onboarding-item">
                <div className="landing-onboarding-num">{item.step}</div>
                <div>
                  <h4 className="landing-onboarding-item-title">{item.title}</h4>
                  <p className="landing-onboarding-item-desc">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="landing-onboarding-footer">
            <span>
              📍 Convocatoria orientada a talleres físicos de <strong>Guayaquil, Samborondón, Daule, Santa Elena, La Libertad y Salinas</strong>.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
