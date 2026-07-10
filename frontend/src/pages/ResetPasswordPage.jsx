import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const token = new URLSearchParams(window.location.search).get("token");
  const [form, setForm] = useState({ new_password: "", confirm_password: "" });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) return setError("Token invalido o faltante en la URL.");
    if (form.new_password.length < 8) return setError("La contrasena debe tener al menos 8 caracteres.");
    if (form.new_password !== form.confirm_password) return setError("Las contrasenas no coinciden.");

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: form.new_password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
      setSuccess(true);
    } catch (err) {
      setError(err.message || "No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="login-portal">
        <div className="login-card" style={{ maxWidth: 420, textAlign: "center" }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--danger)" }}>Enlace invalido</h2>
          <p style={{ fontSize: 13, color: "var(--text2)", marginTop: 10 }}>El enlace de recuperacion es invalido o no contiene un token.</p>
          <button className="btn-secondary" style={{ marginTop: 24, width: "100%" }} onClick={() => navigate("/login")}>
            Volver al login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="login-portal">
      <div className="login-card" style={{ maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text1)" }}>Crear Nueva Contrasena</h2>
          <p style={{ fontSize: 13, color: "var(--text2)", marginTop: 6, lineHeight: 1.5 }}>Ingresa tu nueva contrasena para acceder a tu cuenta.</p>
        </div>

        {success ? (
          <div style={{ textAlign: "center" }}>
            <div className="admin-success-bar" style={{ marginBottom: 20, justifyContent: "center" }}>
              <span>OK</span> Contrasena actualizada correctamente
            </div>
            <button className="btn-primary" onClick={() => navigate("/login")}>
              Ir a iniciar sesion
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="admin-error-bar" style={{ marginBottom: 20 }}>
                <span>ERROR</span> {error}
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Nueva Contrasena</label>
              <div style={{ position: "relative" }}>
                <input className="form-input mono" name="new_password" type={showPassword ? "text" : "password"} placeholder="Minimo 8 caracteres" value={form.new_password} onChange={handleChange} autoComplete="new-password" />
                <button type="button" onClick={() => setShowPassword(!showPassword)} style={{ position: "absolute", color: "#C9A84C", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer" }}>
                  {showPassword ? "Ocultar" : "Ver"}
                </button>
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 28 }}>
              <label className="form-label">Confirmar Contrasena</label>
              <input className="form-input mono" name="confirm_password" type={showPassword ? "text" : "password"} placeholder="Repite la contrasena" value={form.confirm_password} onChange={handleChange} autoComplete="new-password" />
            </div>

            <button className="btn-primary" type="submit" disabled={loading || !form.new_password || !form.confirm_password}>
              {loading ? "Guardando..." : "Actualizar contrasena"}
            </button>
          </form>
        )}
      </div>
      <p style={{ marginTop: 24, fontSize: 11, color: "var(--text3)" }}>
        Impulsado por <span style={{ color: "var(--text2)" }}>K-Atom Solutions</span> | TecniDesk
      </p>
    </div>
  );
}
