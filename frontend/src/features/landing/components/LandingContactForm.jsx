import { useState } from "react";

// Número de WhatsApp oficial para la postulación al programa piloto
// Formato internacional sin '+' para wa.me: 593960029253
const PILOT_WHATSAPP_RAW = "593960029253";
const PILOT_WHATSAPP_DISPLAY = "+593 96 002 9253";

export default function LandingContactForm() {
  const [formData, setFormData] = useState({
    shopName: "",
    contactName: "",
    city: "Guayaquil",
    phone: "",
    weeklyVolume: "10-30 equipos",
    notes: ""
  });

  const [copiedNumber, setCopiedNumber] = useState(false);
  const [copiedMessage, setCopiedMessage] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  // Genera el mensaje estructurado para WhatsApp
  const generateMessage = () => {
    const sName = formData.shopName.trim() || "[Nombre de mi taller]";
    const cName = formData.contactName.trim() || "[Mi nombre]";
    const phone = formData.phone.trim() || "[Mi teléfono]";
    const city = formData.city;
    const vol = formData.weeklyVolume;
    const notes = formData.notes.trim();

    let msg = `Hola equipo TecniDesk,\n\nQuisiera postular a mi taller al Programa Piloto en ${city}:\n\n` +
      `• Taller: ${sName}\n` +
      `• Contacto: ${cName}\n` +
      `• Ciudad: ${city}\n` +
      `• WhatsApp / Teléfono: ${phone}\n` +
      `• Volumen estimado: ${vol}`;

    if (notes) {
      msg += `\n• Comentarios: ${notes}`;
    }

    msg += `\n\n¿Cuáles son los siguientes pasos para coordinar la prueba piloto? Gracias.`;
    return msg;
  };

  const handleOpenWhatsApp = (e) => {
    e.preventDefault();
    const msg = generateMessage();
    const encoded = encodeURIComponent(msg);
    const url = `https://wa.me/${PILOT_WHATSAPP_RAW}?text=${encoded}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleCopyNumber = async () => {
    try {
      await navigator.clipboard.writeText(PILOT_WHATSAPP_DISPLAY);
      setCopiedNumber(true);
      setTimeout(() => setCopiedNumber(false), 2500);
    } catch {
      // Fallback si clipboard API no está permitida
    }
  };

  const handleCopyMessage = async () => {
    try {
      await navigator.clipboard.writeText(generateMessage());
      setCopiedMessage(true);
      setTimeout(() => setCopiedMessage(false), 2500);
    } catch {
      // Fallback
    }
  };

  return (
    <section id="postular" className="landing-section landing-section-alt">
      <div className="landing-container">
        <div className="landing-section-header">
          <div className="landing-badge">Postulación al Piloto</div>
          <h2 className="landing-title">
            Postula tu taller para la prueba en Guayaquil y Santa Elena
          </h2>
          <p className="landing-desc">
            Completa los datos de tu taller. Nos pondremos en contacto directo contigo para coordinar el mes bonificado y la puesta en marcha.
          </p>
        </div>

        <div className="landing-cta-box">
          <form onSubmit={handleOpenWhatsApp}>
            <div className="landing-form-grid">
              <div className="landing-form-group">
                <label className="landing-form-label" htmlFor="shopName">
                  Nombre del taller *
                </label>
                <input
                  id="shopName"
                  name="shopName"
                  className="landing-form-input"
                  type="text"
                  placeholder="Ej. ElectroFix Guayaquil"
                  value={formData.shopName}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="landing-form-group">
                <label className="landing-form-label" htmlFor="contactName">
                  Tu nombre y apellido *
                </label>
                <input
                  id="contactName"
                  name="contactName"
                  className="landing-form-input"
                  type="text"
                  placeholder="Ej. Christian Andrade"
                  value={formData.contactName}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="landing-form-group">
                <label className="landing-form-label" htmlFor="city">
                  Ciudad / Ubicación del taller *
                </label>
                <select
                  id="city"
                  name="city"
                  className="landing-form-select"
                  value={formData.city}
                  onChange={handleChange}
                >
                  <option value="Guayaquil">Guayaquil</option>
                  <option value="Santa Elena">Santa Elena (Capital)</option>
                  <option value="La Libertad">La Libertad</option>
                  <option value="Salinas">Salinas</option>
                  <option value="Samborondón">Samborondón</option>
                  <option value="Daule">Daule</option>
                  <option value="Otra">Otra localidad</option>
                </select>
              </div>

              <div className="landing-form-group">
                <label className="landing-form-label" htmlFor="phone">
                  WhatsApp de contacto *
                </label>
                <input
                  id="phone"
                  name="phone"
                  className="landing-form-input"
                  type="tel"
                  placeholder="Ej. 099 123 4567"
                  value={formData.phone}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="landing-form-group">
                <label className="landing-form-label" htmlFor="weeklyVolume">
                  Equipos recibidos por semana
                </label>
                <select
                  id="weeklyVolume"
                  name="weeklyVolume"
                  className="landing-form-select"
                  value={formData.weeklyVolume}
                  onChange={handleChange}
                >
                  <option value="5-15 equipos/sem">5 a 15 equipos / semana</option>
                  <option value="15-35 equipos/sem">15 a 35 equipos / semana</option>
                  <option value="35-60 equipos/sem">35 a 60 equipos / semana</option>
                  <option value="60+ equipos/sem">Más de 60 equipos / semana</option>
                </select>
              </div>

              <div className="landing-form-group">
                <label className="landing-form-label" htmlFor="notes">
                  ¿Especialidad principal? (Opcional)
                </label>
                <input
                  id="notes"
                  name="notes"
                  className="landing-form-input"
                  type="text"
                  placeholder="Ej. Laptops, smartphones, micro-soldadura..."
                  value={formData.notes}
                  onChange={handleChange}
                />
              </div>

              <div className="landing-form-full" style={{ marginTop: "0.5rem" }}>
                <button
                  type="submit"
                  className="landing-btn landing-btn-whatsapp landing-btn-lg"
                  style={{ width: "100%" }}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/>
                  </svg>
                  Enviar Postulación vía WhatsApp
                </button>
              </div>
            </div>
          </form>

          {/* ─── FALLBACK WIDGET PARA DESKTOP O SIN WHATSAPP WEB ──────────── */}
          <div className="landing-fallback-widget">
            <div className="landing-fallback-title">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                <path d="M7 15h10M7 9h10"></path>
              </svg>
              <span>¿No tienes WhatsApp Web abierto en tu PC? Alternativa directa</span>
            </div>

            <div className="landing-fallback-row">
              <div>
                <span style={{ fontSize: "0.8125rem", color: "var(--text-tertiary)" }}>
                  Escríbenos directamente al número:
                </span>
                <div className="landing-fallback-number">{PILOT_WHATSAPP_DISPLAY}</div>
              </div>

              <button
                type="button"
                onClick={handleCopyNumber}
                className="landing-btn landing-btn-secondary landing-btn-sm"
              >
                {copiedNumber ? "✓ Número copiado" : "Copiar número"}
              </button>
            </div>

            <div style={{ marginTop: "0.5rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
                  Mensaje sugerido pre-armado:
                </span>
                <button
                  type="button"
                  onClick={handleCopyMessage}
                  className="landing-btn landing-btn-outline landing-btn-sm"
                  style={{ padding: "0.25rem 0.6rem", fontSize: "0.75rem" }}
                >
                  {copiedMessage ? "✓ Mensaje copiado" : "Copiar mensaje"}
                </button>
              </div>

              <pre className="landing-fallback-msg-box">
                {generateMessage()}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
