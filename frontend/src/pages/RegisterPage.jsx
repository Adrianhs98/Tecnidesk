import { useState } from "react";
import { Store } from "lucide-react";
import { useNavigate } from "react-router-dom";
import TicketSuccessModal from "../components/shared/TicketSuccessModal";
import { API_BASE } from "../api/config";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ shop_name: "", email: "", contact_whatsapp: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [registered, setRegistered] = useState(null);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const isValid = 
    form.shop_name.trim().length >= 2 && 
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim()) &&
    form.contact_whatsapp.trim().length >= 10;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) {
      setError("Por favor completa todos los campos correctamente.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          shop_name: form.shop_name.trim(), 
          email: form.email.trim(),
          contact_whatsapp: form.contact_whatsapp.trim() 
        }),
      });

      if (res.status === 409) throw new Error("Ya existe un taller registrado con ese correo electronico.");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const data = await res.json();
      setRegistered(data);
    } catch (err) {
      setError(err.message || "No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-portal">
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "var(--surface)", border: "1px solid var(--border2)", borderRadius: 999, padding: "5px 16px 5px 10px", marginBottom: 20 }}>
          <div className="logo-dot" />
          <span style={{ fontSize: 11, fontWeight: 500, color: "var(--text2)", letterSpacing: "0.08em", textTransform: "uppercase" }}>TecniDesk</span>
        </div>
        <h1 style={{ fontSize: "clamp(22px,4vw,30px)", fontWeight: 700, color: "var(--text1)", lineHeight: 1.2 }}>
          Registra tu <span style={{ color: "var(--accent)" }}>Taller</span>
        </h1>
        <p style={{ color: "var(--text2)", marginTop: 8, fontSize: 14, fontWeight: 300, lineHeight: 1.6 }}>Crea tu cuenta en TecniDesk y empieza a gestionar tus tickets hoy mismo.</p>
      </div>

      <div className="login-card" style={{ maxWidth: 460 }}>
        <div style={{ width: 56, height: 56, borderRadius: 16, background: "rgba(201,167,106,0.10)", border: "1px solid rgba(201,167,106,0.22)", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20 }}>
          <Store size={22} color="var(--accent)" />
        </div>

        <div style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text1)" }}>Nuevo Taller</h2>
          <p style={{ fontSize: 13, color: "var(--text2)", marginTop: 4 }}>Recibiras una contrasena generada automaticamente.</p>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="admin-error-bar" style={{ marginBottom: 20 }}>
              <span>ERROR</span> {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Nombre del Taller <span style={{ color: "var(--accent)" }}>*</span></label>
            <input className="form-input" name="shop_name" type="text" placeholder="ej. TecniCenter Guayaquil" value={form.shop_name} onChange={handleChange} autoComplete="organization" />
            <p className="form-hint">Minimo 2 caracteres. Este nombre aparecera en tus tickets.</p>
          </div>

          <div className="form-group">
            <label className="form-label">Correo Electronico <span style={{ color: "var(--accent)" }}>*</span></label>
            <input className="form-input" name="email" type="email" placeholder="taller@correo.com" value={form.email} onChange={handleChange} autoComplete="email" />
            <p className="form-hint">Sera tu usuario para iniciar sesion.</p>
          </div>

          <div className="form-group" style={{ marginBottom: 28 }}>
            <label className="form-label">WhatsApp de Contacto <span style={{ color: "var(--accent)" }}>*</span></label>
            <input className="form-input" name="contact_whatsapp" type="tel" placeholder="ej. 593991234567" value={form.contact_whatsapp} onChange={handleChange} />
            <p className="form-hint">Formato internacional sin el símbolo +. Ejemplo: 593987654321</p>
          </div>

          <button className="btn-primary" type="submit" disabled={loading || !isValid}>
            {loading ? "Registrando..." : "Crear cuenta"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "var(--text3)" }}>
          Ya tienes cuenta?{" "}
          <button onClick={() => navigate("/login")} style={{ background: "none", border: "none", color: "var(--accent)", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600, padding: 0 }}>
            Iniciar sesion
          </button>
        </p>
      </div>

      <p style={{ marginTop: 24, fontSize: 11, color: "var(--text3)" }}>
        Impulsado por <span style={{ color: "var(--text2)" }}>TecniDesk</span>
      </p>

      {registered && <TicketSuccessModal ticket={registered} onClose={() => { setRegistered(null); navigate("/login"); }} />}
    </div>
  );
}
