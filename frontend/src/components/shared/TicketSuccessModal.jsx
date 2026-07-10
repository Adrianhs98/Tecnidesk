import { useState } from "react";

export default function TicketSuccessModal({ ticket, onClose }) {
  const [copied, setCopied] = useState(false);
  const code = ticket.generated_password || ticket.tracking_token || "-";
  const titleBody = ticket.shop_name
    ? (
      <>
        El taller <strong style={{ color: "var(--text1)" }}>{ticket.shop_name}</strong> ha sido registrado con exito.
      </>
      )
    : (
      <>
        El equipo <strong style={{ color: "var(--text1)" }}>{ticket.device_brand} {ticket.device_model}</strong> ha sido registrado.
      </>
      );

  const codeLabel = ticket.shop_name ? "CONTRASENA GENERADA" : "CODIGO DE ACCESO / RASTREO";

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-card" style={{ maxWidth: 420, padding: "36px 32px", textAlign: "center", border: "1px solid rgba(201,167,106,0.28)" }}>
        <div style={{ width: 72, height: 72, borderRadius: "50%", background: "rgba(78,159,125,0.12)", border: "1px solid rgba(78,159,125,0.28)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, margin: "0 auto 20px" }}>OK</div>

        <h2 style={{ fontSize: 22, fontWeight: 700, color: "var(--text1)", marginBottom: 10 }}>Registro Exitoso</h2>
        <p style={{ fontSize: 14, color: "var(--text2)", lineHeight: 1.6, marginBottom: 24 }}>{titleBody}</p>

        <div style={{ background: "var(--bg)", border: "1px dashed var(--accent)", borderRadius: 14, padding: "20px 24px", marginBottom: 24, position: "relative" }}>
          <span style={{ fontSize: 10, fontWeight: 600, color: "var(--text3)", letterSpacing: "0.1em", textTransform: "uppercase", display: "block", marginBottom: 10 }}>{codeLabel}</span>
          <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: code.length > 20 ? 13 : 22, color: "var(--accent)", fontWeight: 700, wordBreak: "break-all", display: "block", lineHeight: 1.4 }}>
            {code}
          </code>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button className="btn-primary" onClick={handleCopy} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
            {copied ? "Copiado" : `Copiar ${ticket.shop_name ? "Contrasena" : "Codigo"}`}
          </button>
          <button className="btn-secondary" onClick={onClose} style={{ width: "100%" }}>
            Cerrar y continuar
          </button>
        </div>

        <p style={{ fontSize: 11, color: "var(--text3)", marginTop: 20, lineHeight: 1.5 }}>
          Guarda {ticket.shop_name ? "esta contrasena" : "este codigo"} en un lugar seguro.
        </p>
      </div>
    </div>
  );
}
