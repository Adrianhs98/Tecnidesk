import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Por favor ingresa un correo electronico valido.");
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const res = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
      setMessage(data.message || "Si el email existe recibiras instrucciones en tu correo.");
    } catch (err) {
      setError(err.message || "No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-portal">
      <div className="login-card" style={{ maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text1)" }}>Recuperar Contrasena</h2>
          <p style={{ fontSize: 13, color: "var(--text2)", marginTop: 6, lineHeight: 1.5 }}>Ingresa tu correo y te enviaremos un enlace para crear una nueva contrasena.</p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="admin-error-bar" style={{ marginBottom: 20 }}>
              <span>ERROR</span> {error}
            </div>
          )}
          {message && (
            <div className="admin-success-bar" style={{ marginBottom: 20 }}>
              <span>OK</span> {message}
            </div>
          )}

          <div className="form-group" style={{ marginBottom: 28 }}>
            <label className="form-label">Correo Electronico</label>
            <input className="form-input" type="email" placeholder="taller@correo.com" value={email} onChange={(e) => { setEmail(e.target.value); setError(null); }} autoComplete="email" disabled={loading || !!message} />
          </div>

          <button className="btn-primary" type="submit" disabled={loading || !!message || !email.trim()}>
            {loading ? "Enviando..." : "Enviar instrucciones"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "var(--text3)" }}>
          <button type="button" onClick={() => navigate("/login")} style={{ background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600, padding: 0 }}>
            Volver al login
          </button>
        </p>
      </div>
      <p style={{ marginTop: 24, fontSize: 11, color: "var(--text3)" }}>
        Impulsado por <span style={{ color: "var(--text2)" }}>TecniDesk</span>
      </p>
    </div>
  );
}
