import { useState, useEffect } from "react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { previewDiagnosis } from "../../../api/diagnostic";

const emptyForm = { 
  client_name: "", client_phone: "", client_email: "", 
  device_brand: "", device_model: "", issue_description: "", pin_or_password: "",
  assignment_mode: "unassigned", technician_id: ""
};

export default function NewTicketModal({ onClose, onCreated }) {
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [fetchingPreview, setFetchingPreview] = useState(false);
  
  const [technicians, setTechnicians] = useState([]);
  
  useEffect(() => {
    let mounted = true;
    authFetch(`${API_BASE}/technicians`)
      .then(res => res.ok ? res.json() : [])
      .then(data => { if (mounted) setTechnicians(data); })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const isEmailValid = emailRegex.test(form.client_email.trim());
  const isPhoneValid = !form.client_phone.trim() || /^\+?[0-9]{7,15}$/.test(form.client_phone.trim());

  const handleBlurSymptom = async () => {
    if (form.device_brand && form.device_model && form.issue_description.length > 5) {
      setFetchingPreview(true);
      try {
        const res = await previewDiagnosis(form.device_brand, form.device_model, form.issue_description);
        setPreview(res.suggestion);
      } catch (e) {
        setPreview("");
      } finally {
        setFetchingPreview(false);
      }
    } else {
      setPreview("");
    }
  };

  const isValid = ["client_email", "device_brand", "device_model", "issue_description"].every((key) => form[key].trim().length > 0) && isEmailValid && isPhoneValid;

  const handleSave = async () => {
    if (!["client_email", "device_brand", "device_model", "issue_description"].every((key) => form[key].trim().length > 0)) {
      setError("Todos los campos obligatorios (*) deben estar completos.");
      return;
    }

    if (!isEmailValid) {
      setError("Por favor ingresa un correo electronico valido.");
      return;
    }

    if (!isPhoneValid) {
      setError("Por favor ingresa un numero de telefono valido (de 7 a 15 digitos).");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const payload = {
        client_email: form.client_email,
        client_name: form.client_name.trim() || form.client_email,
        client_phone: form.client_phone.trim() || "",
        device_brand: form.device_brand,
        device_model: form.device_model,
        issue_description: form.issue_description,
        ...(form.pin_or_password.trim() && { pin_or_password: form.pin_or_password.trim() }),
        assignment_mode: form.assignment_mode,
        ...(form.assignment_mode === "manual" && form.technician_id && { technician_id: form.technician_id })
      };

      const res = await authFetch(`${API_BASE}/tickets`, {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const warning = res.headers.get("X-Assignment-Warning");
      if (warning) {
        alert("Advertencia: " + warning);
      }

      const ticket = await res.json();
      
      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        const token = sessionStorage.getItem("td_token");
        const uploadRes = await fetch(`${API_BASE}/tickets/${ticket.id}/evidences`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${token}` },
          body: formData,
        });
        if (uploadRes.ok) {
          const evidence = await uploadRes.json();
          ticket.evidences = [evidence];
        } else {
          console.error("Fallo al subir la evidencia inicial");
        }
      }

      onCreated(ticket);
    } catch (err) {
      setError(err.message || "No se pudo crear el ticket. Verifica la conexion.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-card">
        <div className="modal-header">
          <div>
            <div className="modal-title">Ingresar Nuevo Equipo</div>
            <div className="modal-subtitle">Completa los datos del cliente y el dispositivo</div>
          </div>
          <button className="modal-close" onClick={onClose}>X</button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="admin-error-bar">
              <span>ERROR</span> {error}
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Nombre del cliente <span style={{ color: "var(--text3)" }}>(opcional)</span></label>
              <input className="form-input" name="client_name" type="text" placeholder="ej. Juan Perez" value={form.client_name} onChange={handleChange} />
              <p className="form-hint">Si no se ingresa, se usara el correo.</p>
            </div>
            <div className="form-group">
              <label className="form-label">Telefono <span style={{ color: "var(--text3)" }}>(opcional)</span></label>
              <input className="form-input mono" name="client_phone" type="tel" placeholder="ej. 0991234567" value={form.client_phone} onChange={handleChange} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Correo del cliente <span style={{ color: "var(--accent)" }}>*</span></label>
            <input className="form-input" name="client_email" type="email" placeholder="cliente@correo.com" value={form.client_email} onChange={handleChange} />
            <p className="form-hint">Se usara para enviar notificaciones automaticas.</p>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Marca <span style={{ color: "var(--accent)" }}>*</span></label>
              <input className="form-input" name="device_brand" type="text" placeholder="ej. Samsung" value={form.device_brand} onChange={handleChange} />
            </div>
            <div className="form-group">
              <label className="form-label">Modelo <span style={{ color: "var(--accent)" }}>*</span></label>
              <input className="form-input" name="device_model" type="text" placeholder="ej. Galaxy S22" value={form.device_model} onChange={handleChange} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Descripcion del problema <span style={{ color: "var(--accent)" }}>*</span></label>
            <textarea 
              className="form-textarea" 
              name="issue_description" 
              placeholder="Describe el problema reportado por el cliente..." 
              value={form.issue_description} 
              onChange={handleChange} 
              onBlur={handleBlurSymptom}
            />
            {fetchingPreview && <div style={{ fontSize: 11, color: "var(--text3)", marginTop: 4 }}>Analizando...</div>}
            {preview && !fetchingPreview && (
              <div style={{ marginTop: 6, fontSize: 12, background: "rgba(91,192,222,0.1)", border: "1px solid var(--accent)", padding: "6px 10px", borderRadius: 6, color: "var(--accent)" }}>
                <strong>IA Sugiere:</strong> {preview}
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Contrasena o PIN del dispositivo <span style={{ color: "var(--text3)" }}>(opcional)</span></label>
            <input className="form-input mono" name="pin_or_password" type="text" placeholder="ej. 1234 o patron" value={form.pin_or_password} onChange={handleChange} />
            <p className="form-hint">Se almacena cifrado y solo el tecnico puede verlo.</p>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Asignación de Técnico</label>
              <select className="status-select" name="assignment_mode" value={form.assignment_mode} onChange={handleChange}>
                <option value="unassigned">Sin asignar</option>
                <option value="random">Automático (menor carga)</option>
                <option value="manual">Manual</option>
              </select>
            </div>
            {form.assignment_mode === "manual" && (
              <div className="form-group">
                <label className="form-label">Técnico Seleccionado</label>
                <select className="status-select" name="technician_id" value={form.technician_id} onChange={handleChange}>
                  <option value="">Seleccione...</option>
                  {technicians.map(t => (
                    <option key={t.id} value={t.id}>{t.full_name} {t.declared_specialty ? `(${t.declared_specialty})` : ""}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">Evidencia Fotográfica inicial <span style={{ color: "var(--text3)" }}>(opcional)</span></label>
            <input className="form-input" type="file" accept="image/jpeg, image/png, image/webp" onChange={(e) => setFile(e.target.files[0])} />
            <p className="form-hint">Máx 2MB (JPG, PNG, WEBP). Se subirá al guardar el equipo.</p>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose} disabled={saving}>Cancelar</button>
          <button className="btn-primary" style={{ width: "auto", padding: "11px 24px" }} onClick={handleSave} disabled={saving || !isValid}>
            {saving ? "Guardando..." : "Guardar ticket"}
          </button>
        </div>
      </div>
    </div>
  );
}
