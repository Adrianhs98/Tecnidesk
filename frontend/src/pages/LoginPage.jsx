import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../api/config";
import ThemeToggle from "../components/shared/ThemeToggle";

export default function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (loading) return;

    const email = form.username.trim().toLowerCase();
    if (!email || !form.password.trim()) {
      setError("Por favor completa todos los campos.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: form.password }),
      });

      if (!res.ok) throw new Error("Credenciales incorrectas");

      const data = await res.json();
      sessionStorage.setItem("td_token", data.access_token);
      if (data.shop_name) {
        sessionStorage.setItem("td_shop", data.shop_name);
      }
      const role = data.role || "admin";
      sessionStorage.setItem("td_role", role);
      sessionStorage.setItem("td_user_name", data.user_full_name || "");

      if (role === "technician") {
        navigate("/tech");
      } else {
        navigate("/admin");
      }
    } catch {
      setError("Credenciales incorrectas o servidor inactivo.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-portal" style={{ position: "relative" }}>
      <div style={{ position: "absolute", top: 16, right: 16 }}>
        <ThemeToggle />
      </div>
      <div className="login-card">
        <div className="login-card-header">
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "var(--bg-surface)", border: "1px solid var(--border-strong)", borderRadius: 999, padding: "5px 14px 5px 9px" }}>
            <div className="logo-dot" />
            <span style={{ fontSize: 11, fontWeight: 500, color: "var(--text-secondary)", letterSpacing: "0.08em", textTransform: "uppercase" }}>TecniDesk Admin</span>
          </div>
          <h2>Panel de Control</h2>
          <p>Ingresa tus credenciales para continuar</p>
        </div>

        {error && (
          <div className="admin-error-bar" style={{ marginBottom: 20 }}>
            <span>ERROR</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Usuario o Correo</label>
            <input
              className="form-input"
              name="username"
              type="text"
              placeholder="taller@correo.com"
              value={form.username}
              onChange={handleChange}
              autoComplete="username"
              required
            />
          </div>

          <div className="form-group" style={{ marginBottom: 24 }}>
            <label className="form-label">Contrasena</label>
            <div style={{ position: "relative" }}>
              <input
                className="form-input mono"
                name="password"
                type={showPassword ? "text" : "password"}
                placeholder="********"
                value={form.password}
                onChange={handleChange}
                autoComplete="current-password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                style={{ position: "absolute", color: "var(--color-accent)", right: "12px", top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer" }}
              >
                {showPassword ? "Ocultar" : "Ver"}
              </button>
            </div>
          </div>

          <button type="submit" className="btn-primary" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Verificando..." : "Ingresar"}
          </button>
        </form>

        <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "var(--text-tertiary)" }}>
          Olvidaste tu contrasena?{" "}
          <button
            type="button"
            onClick={() => navigate("/forgot-password")}
            style={{ background: "none", border: "none", color: "var(--color-accent)", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600, padding: 0 }}
          >
            Recuperar aqui
          </button>
        </p>

        <p style={{ textAlign: "center", marginTop: 12, fontSize: 12, color: "var(--text-tertiary)" }}>Acceso exclusivo para personal autorizado</p>
      </div>

      <p style={{ marginTop: 24, fontSize: 11, color: "var(--text-tertiary)" }}>
        Impulsado por <span style={{ color: "var(--text-secondary)" }}>TecniDesk</span>
      </p>
    </div>
  );
}
