export default function LandingPainRelief() {
  const workshopPains = [
    {
      badge: "Interrupciones",
      title: "Mensajes a deshoras en WhatsApp",
      desc: "El cliente llamando o escribiendo a toda hora preguntando «¿ya está listo mi equipo?», sacando al técnico del microscopio.",
      impact: "Pérdida de concentración y horas de trabajo desperdiciadas."
    },
    {
      badge: "Seguridad",
      title: "PINs en masking tape que se borran",
      desc: "Contraseñas y patrones anotados en cinta adhesiva que se caen, se manchan con alcohol isopropílico o quedan a la vista de cualquiera.",
      impact: "Riesgo de reclamos por privacidad y pérdida de tiempo pidiendo el PIN de nuevo."
    },
    {
      badge: "Tiempos",
      title: "Equipos olvidados en percha",
      desc: "Dispositivos que pasan 10 o 15 días en el taller sin diagnóstico simplemente porque nadie recuerda cuándo ingresaron.",
      impact: "Clientes molestos y cuellos de botella sin visibilidad."
    },
    {
      badge: "Cobranza",
      title: "Presupuestos que quedan en visto",
      desc: "Cotizaciones enviadas en audios o textos de WhatsApp que se pierden en el chat, sin aprobación formal ni constancia de repuestos.",
      impact: "Dudas sobre si comprar el repuesto o dejar el equipo desarmado."
    },
    {
      badge: "Conocimiento",
      title: "El conocimiento se va con el técnico",
      desc: "La solución difícil que un técnico descubrió hoy no queda anotada en ningún lado. Cuando entra una falla similar, hay que investigar de cero.",
      impact: "Mismo tiempo invertido dos veces en la misma falla."
    }
  ];

  const transformationSteps = [
    {
      step: "01",
      phase: "Recepción",
      before: "Anotar en libreta, masking tape con PIN a mano, sin fotos del estado estético.",
      after: "Ticket digital en 20 segundos, fotos de ingreso, PIN cifrado con Fernet y comprobante al cliente."
    },
    {
      step: "02",
      phase: "Diagnóstico",
      before: "El técnico busca diagramas en grupos de Telegram y adivina el tiempo de entrega.",
      after: "Semáforo SLA activo, evidencias fotográficas de banco y sugerencias de fallas previas con Ohm."
    },
    {
      step: "03",
      phase: "Aprobación",
      before: "Enviar mensaje informal por WhatsApp esperando respuesta que queda en visto.",
      after: "Portal de tracking propio: el cliente ve la foto de la falla, el repuesto y aprueba con 1 clic."
    },
    {
      step: "04",
      phase: "Reparación",
      before: "Piezas mezcladas en cajas sin control de qué repuesto se usó en cada equipo.",
      after: "Descuento de inventario enlazado al ticket con costo y número de parte trazable."
    },
    {
      step: "05",
      phase: "Cierre y Entrega",
      before: "Reclamos por rayones previos o desacuerdos sobre qué se reparó realmente.",
      after: "Historial inmutable con fotos de entrega, garantía registrada y cliente satisfecho."
    }
  ];

  return (
    <section id="solucion" className="landing-section landing-section-alt">
      <div className="landing-container">
        {/* Header */}
        <div className="landing-section-header">
          <div className="landing-badge">El Día a Día en el Taller</div>
          <h2 className="landing-title">
            Tu taller pierde dinero en el desorden, no en la reparación
          </h2>
          <p className="landing-desc">
            Reparar placas y cambiar pantallas es tu especialidad. Pero el desorden de libretas, chats y perchas desorganizadas te cuesta clientes y tranquilidad.
          </p>
        </div>

        {/* Real Workshop Scenarios Grid */}
        <div className="landing-workshop-realities">
          <div className="landing-realities-header">
            <span className="landing-realities-icon">⚠️</span>
            <h3>Esto pasa a diario en un taller convencional</h3>
          </div>
          <div className="landing-realities-grid">
            {workshopPains.map((item, idx) => (
              <div key={idx} className="landing-reality-card">
                <div className="landing-reality-badge">{item.badge}</div>
                <h4 className="landing-reality-title">{item.title}</h4>
                <p className="landing-reality-desc">{item.desc}</p>
                <div className="landing-reality-impact">
                  <strong>Consecuencia:</strong> {item.impact}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Operational Transformation Visual Track */}
        <div className="landing-transformation-box">
          <div className="landing-transformation-header">
            <div className="landing-transformation-title-wrap">
              <span className="landing-transformation-pill">Transformación Operativa</span>
              <h3 className="landing-transformation-title">
                Del caos de libretas a la trazabilidad completa
              </h3>
            </div>
            <p className="landing-transformation-sub">
              Así cambia el recorrido de cada equipo dentro de tu taller:
            </p>
          </div>

          <div className="landing-flow-timeline">
            {transformationSteps.map((step, idx) => (
              <div key={idx} className="landing-flow-node">
                <div className="landing-flow-node-index">
                  <span>{step.step}</span>
                  <div className="landing-flow-node-phase">{step.phase}</div>
                </div>

                <div className="landing-flow-node-content">
                  <div className="landing-flow-before">
                    <span className="landing-flow-label-before">Antes (Caos manual)</span>
                    <p>{step.before}</p>
                  </div>

                  <div className="landing-flow-arrow">➔</div>

                  <div className="landing-flow-after">
                    <span className="landing-flow-label-after">Con TecniDesk</span>
                    <p>{step.after}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
