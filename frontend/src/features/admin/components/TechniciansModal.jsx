import { useEffect, useState } from "react";
import { X, Users, Check, Edit, Trash2 } from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { formatCurrency } from "../../../utils/currency";

export default function TechniciansModal({ onClose }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [view, setView] = useState("list"); // 'list' | 'form'
  const [formData, setFormData] = useState({ id: null, full_name: "", contact: "", declared_specialty: "", email: "", generate_access: false });
  const [formLoading, setFormLoading] = useState(false);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`${API_BASE}/technicians/metrics`);
      if (!res.ok) throw new Error("Error al cargar métricas");
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    try {
      const isEdit = !!formData.id;
      const url = isEdit ? `${API_BASE}/technicians/${formData.id}` : `${API_BASE}/technicians`;
      const method = isEdit ? "PATCH" : "POST";
      
      const payload = {
        full_name: formData.full_name,
        contact: formData.contact || null,
        declared_specialty: formData.declared_specialty || null
      };

      if (!isEdit && formData.generate_access) {
        payload.generate_access = true;
        payload.email = formData.email;
      }

      const res = await authFetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || "Error al guardar");
      }

      await fetchMetrics();
      setView("list");
    } catch (err) {
      alert(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  const handleGenerateAccess = async (techId) => {
    const email = window.prompt("Ingrese el correo del técnico para generar su acceso:");
    if (!email) return;

    try {
      const res = await authFetch(`${API_BASE}/technicians/${techId}/access`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error al generar acceso");
      }
      alert("Acceso generado exitosamente.");
      fetchMetrics();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeactivate = async (id) => {
    if(!window.confirm("¿Seguro que deseas desactivar este técnico?")) return;
    try {
      const res = await authFetch(`${API_BASE}/technicians/${id}`, { method: "DELETE" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error al desactivar");
      }
      fetchMetrics();
    } catch (err) {
      alert(err.message);
    }
  };
  
  const handleReactivate = async (id) => {
    try {
      const res = await authFetch(`${API_BASE}/technicians/${id}/reactivate`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error al reactivar");
      }
      fetchMetrics();
    } catch (err) {
      alert(err.message);
    }
  };

  const renderList = () => (
    <>
      {error && <div className="error-card">{error}</div>}
      
      {metrics && metrics.shop_totals && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
          <div className="admin-stat-card" style={{ padding: "12px" }}>
            <div className="admin-stat-label">Total Tickets (Taller)</div>
            <div className="admin-stat-value accent" style={{ fontSize: "20px" }}>{metrics.shop_totals.total_tickets}</div>
          </div>
          <div className="admin-stat-card" style={{ padding: "12px" }}>
            <div className="admin-stat-label">Valor Entregado</div>
            <div className="admin-stat-value success" style={{ fontSize: "20px" }}>{formatCurrency(metrics.shop_totals.total_delivered)}</div>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: "10px", flexDirection: "column" }}>
        {metrics?.technicians.map(tech => (
          <div key={tech.id} style={{ 
            background: "var(--surface2)", 
            border: "1px solid var(--border)", 
            borderRadius: "12px", 
            padding: "16px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            opacity: tech.is_active ? 1 : 0.6
          }}>
            <div>
              <div style={{ fontSize: "15px", fontWeight: "600", color: "var(--text1)", display: "flex", alignItems: "center", gap: "8px" }}>
                {tech.full_name} 
                {!tech.is_active && <span style={{ fontSize: "10px", padding: "2px 6px", background: "var(--danger)", color: "#fff", borderRadius: "4px" }}>INACTIVO</span>}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text3)", marginTop: "4px" }}>
                {tech.contact ? `${tech.contact} • ` : ""}
                {tech.declared_specialty || "Sin especialidad"}
              </div>
              
              <div style={{ display: "flex", gap: "16px", marginTop: "12px" }}>
                <div style={{ fontSize: "12px", color: "var(--text2)" }}>
                  Activos: <strong style={{ color: "var(--accent)" }}>{tech.active_tickets}</strong>
                </div>
                <div style={{ fontSize: "12px", color: "var(--text2)" }}>
                  Histórico: <strong>{tech.total_tickets}</strong>
                </div>
                <div style={{ fontSize: "12px", color: "var(--text2)" }}>
                  Valor asignado: <strong>{formatCurrency(tech.attributed_value)}</strong>
                </div>
              </div>

              {tech.inferred_specialties && tech.inferred_specialties.length > 0 && (
                <div style={{ marginTop: "12px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
                  {tech.inferred_specialties.map(spec => (
                    <span key={spec.category} title={`${spec.count} tickets de ${spec.category}`} style={{ background: "rgba(255,255,255,0.05)", border: "1px solid var(--border)", padding: "4px 8px", borderRadius: "12px", fontSize: "11px", display: "flex", gap: "4px", alignItems: "center" }}>
                      {spec.emoji} {spec.category}
                    </span>
                  ))}
                </div>
              )}
            </div>
            
            <div style={{ display: "flex", gap: "8px", flexDirection: "column" }}>
              <button className="btn-secondary" style={{ padding: "6px 10px" }} onClick={() => {
                setFormData({ id: tech.id, full_name: tech.full_name, contact: tech.contact || "", declared_specialty: tech.declared_specialty || "", email: "", generate_access: false });
                setView("form");
              }} title="Editar Técnico">
                <Edit size={14} />
              </button>
              {tech.is_active && !tech.user_id && (
                <button className="btn-secondary" style={{ padding: "6px 10px", color: "var(--accent)", borderColor: "var(--accent)" }} onClick={() => handleGenerateAccess(tech.id)} title="Generar acceso">
                  <Users size={14} />
                </button>
              )}
              {tech.is_active ? (
                <button className="btn-danger" style={{ padding: "6px 10px" }} onClick={() => handleDeactivate(tech.id)} title="Desactivar Técnico">
                  <Trash2 size={14} />
                </button>
              ) : (
                <button className="btn-secondary" style={{ padding: "6px 10px", color: "var(--success)", borderColor: "var(--success)" }} onClick={() => handleReactivate(tech.id)} title="Reactivar Técnico">
                  <Check size={14} />
                </button>
              )}
            </div>
          </div>
        ))}
        {metrics?.technicians.length === 0 && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text3)" }}>
            No hay técnicos registrados en este taller.
          </div>
        )}
      </div>
    </>
  );

  const renderForm = () => (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div className="form-group">
        <label className="form-label">Nombre Completo *</label>
        <input 
          required 
          className="form-input" 
          value={formData.full_name} 
          onChange={e => setFormData({...formData, full_name: e.target.value})} 
          placeholder="Ej: Juan Pérez"
        />
      </div>
      <div className="form-group">
        <label className="form-label">Contacto (Opcional)</label>
        <input 
          className="form-input" 
          value={formData.contact} 
          onChange={e => setFormData({...formData, contact: e.target.value})} 
          placeholder="Teléfono o email"
        />
      </div>
      <div className="form-group">
        <label className="form-label">Especialidad Declarada (Opcional)</label>
        <input 
          className="form-input" 
          value={formData.declared_specialty} 
          onChange={e => setFormData({...formData, declared_specialty: e.target.value})} 
          placeholder="Ej: Microsoldadura, Apple, Pantallas"
        />
      </div>
      
      {!formData.id && (
        <div className="form-group" style={{ background: "var(--surface2)", padding: "16px", borderRadius: "12px", border: "1px solid var(--border)", marginTop: "8px" }}>
          <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", color: "var(--text1)", fontWeight: "500", fontSize: "14px" }}>
            <input 
              type="checkbox" 
              checked={formData.generate_access}
              onChange={e => setFormData({...formData, generate_access: e.target.checked})}
              style={{ accentColor: "var(--accent)" }}
            />
            Grant system access (Generar acceso al sistema)
          </label>
          
          {formData.generate_access && (
            <div style={{ marginTop: "16px" }}>
              <label className="form-label">Correo Electrónico *</label>
              <input 
                required 
                type="email"
                className="form-input" 
                value={formData.email} 
                onChange={e => setFormData({...formData, email: e.target.value})} 
                placeholder="correo@ejemplo.com"
              />
              <p style={{ fontSize: "12px", color: "var(--text3)", marginTop: "6px" }}>
                Se enviará un correo con las credenciales de acceso a esta dirección.
              </p>
            </div>
          )}
        </div>
      )}

      <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
        <button type="button" className="btn-secondary" style={{ flex: 1 }} onClick={() => setView("list")} disabled={formLoading}>Cancelar</button>
        <button type="submit" className="btn-primary" style={{ flex: 1 }} disabled={formLoading}>
          {formLoading ? "Guardando..." : "Guardar Técnico"}
        </button>
      </div>
    </form>
  );

  return (
    <div className="modal-overlay" style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", display: "flex", justifyContent: "center", alignItems: "center", zIndex: 1000, padding: "16px" }}>
      <div className="modal-content" style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "24px", width: "100%", maxWidth: "600px", maxHeight: "90vh", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "24px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "40px", height: "40px", borderRadius: "12px", background: "rgba(201,167,106,0.1)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--accent)" }}>
              <Users size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: "700", color: "var(--text1)" }}>Técnicos</h2>
              <p style={{ fontSize: "12px", color: "var(--text3)" }}>{view === "list" ? "Gestión y métricas del personal" : (formData.id ? "Editar técnico" : "Registrar nuevo técnico")}</p>
            </div>
          </div>
          <div style={{ display: "flex", gap: "12px" }}>
            {view === "list" && (
              <button className="btn-new-ticket" onClick={() => {
                setFormData({ id: null, full_name: "", contact: "", declared_specialty: "", email: "", generate_access: false });
                setView("form");
              }} style={{ padding: "8px 16px", fontSize: "13px" }}>
                + Nuevo Técnico
              </button>
            )}
            <button className="btn-secondary" onClick={onClose} style={{ padding: "8px", borderRadius: "50%", border: "none" }}>
              <X size={20} />
            </button>
          </div>
        </div>
        
        <div style={{ padding: "24px", overflowY: "auto" }}>
          {loading && view === "list" ? (
            <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text3)" }}>Cargando métricas...</div>
          ) : view === "list" ? (
            renderList()
          ) : (
            renderForm()
          )}
        </div>
      </div>
    </div>
  );
}
