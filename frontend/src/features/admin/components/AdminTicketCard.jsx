import { useState, useEffect, useCallback } from "react";
import imageCompression from "browser-image-compression";
import { 
  User, 
  Smartphone, 
  Mail, 
  AlertTriangle, 
  Calendar, 
  Lock, 
  Paperclip, 
  Wrench, 
  ClipboardList, 
  Camera, 
  MessageCircle, 
  X 
} from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { STATUS_CONFIG, ADMIN_STATUSES } from "../../../utils/constants";
import { formatDate } from "../../../utils/date";

export default function AdminTicketCard({ ticket, onStatusChange }) {
  const cfg = STATUS_CONFIG[ticket.status] || { label: ticket.status, color: "var(--accent)", icon: "📋" };
  const [selectedStatus, setSelectedStatus] = useState(ticket.status);
  const [saving, setSaving] = useState(false);

  const [evidences, setEvidences] = useState([]);
  const [loadingEvidences, setLoadingEvidences] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Diagnóstico y presupuesto
  const [showDiagForm, setShowDiagForm] = useState(false);
  const [diagNotes, setDiagNotes] = useState(ticket.diagnostic_notes || "");
  const [diagCost, setDiagCost] = useState(ticket.total_cost || "");
  const [diagSaving, setDiagSaving] = useState(false);
  const [diagError, setDiagError] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    let mounted = true;
    const fetchEvidences = async () => {
      setLoadingEvidences(true);
      try {
        const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/evidences`);
        if (res.ok && mounted) {
          setEvidences(await res.json());
        }
      } catch (err) {
        console.error("Error fetching evidences:", err);
      } finally {
        if (mounted) setLoadingEvidences(false);
      }
    };
    fetchEvidences();
    return () => { mounted = false; };
  }, [ticket.id]);

  const handleUploadEvidence = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadError(null);
    setUploading(true);

    try {
      const options = {
        maxSizeMB: 0.8,
        maxWidthOrHeight: 1200,
        useWebWorker: true,
        initialQuality: 0.8
      };
      const compressedFile = await imageCompression(file, options);

      const formData = new FormData();
      formData.append("file", compressedFile, compressedFile.name || "evidence.jpg");

      const token = sessionStorage.getItem("td_token");
      // Nota: No usamos authFetch aquí porque necesitamos que el navegador setee el boundary del multipart
      const res = await fetch(`${API_BASE}/tickets/${ticket.id}/evidences`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Error ${res.status}`);
      }

      const newEv = await res.json();
      setEvidences(prev => [...prev, newEv]);
    } catch (err) {
      setUploadError(err.message || "Error al subir imagen");
    } finally {
      setUploading(false);
      e.target.value = null;
    }
  };

  const isDirty = selectedStatus !== ticket.status;

  const handleSaveStatus = async () => {
    if (!isDirty) return;
    setSaving(true);
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: selectedStatus }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const updated = await res.json();
      onStatusChange(updated);
    } catch {
      setSelectedStatus(ticket.status); // revert on error
    } finally {
      setSaving(false);
    }
  };

  const handleSendDiagnostic = async () => {
    if (!diagNotes.trim() || diagNotes.trim().length < 5) {
      setDiagError("El diagnóstico debe tener al menos 5 caracteres.");
      return;
    }
    if (!diagCost || parseFloat(diagCost) < 0) {
      setDiagError("Ingresa un costo válido.");
      return;
    }
    setDiagSaving(true);
    setDiagError(null);
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/diagnostic`, {
        method: "PATCH",
        body: JSON.stringify({ diagnostic_notes: diagNotes.trim(), total_cost: parseFloat(diagCost) }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }
      const updated = await res.json();
      onStatusChange(updated);
      setShowDiagForm(false);
    } catch (err) {
      setDiagError(err.message || "Error al enviar diagnóstico.");
    } finally {
      setDiagSaving(false);
    }
  };

  const rawPhone = ticket.customer?.phone_number || ticket._frontendPhone || "";
  const cleanPhone = rawPhone.replace(/\D/g, "").replace(/^0/, "");
  const waPhone = cleanPhone ? "593" + cleanPhone : "";

  // Modal accessibility
  const closeDetail = useCallback(() => setShowDetail(false), []);

  useEffect(() => {
    if (!showDetail) return;
    
    document.body.style.overflow = "hidden";
    
    const handleKeyDown = (e) => {
      if (e.key === "Escape") closeDetail();
    };
    
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = "unset";
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [showDetail, closeDetail]);

  return (
    <>
    <div className="ticket-card">

      {/* HEADER: device name, brand badge, status badge */}
      <div className="ticket-card-header">
        <div style={{ minWidth: 0 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:2 }}>
            <div className="ticket-device-name">{ticket.device_model}</div>
            <span style={{ fontSize:11, background:"var(--bg)", border:"1px solid var(--border)", color:"var(--text3)", padding:"1px 8px", borderRadius:4, fontWeight:700, letterSpacing:"0.05em", textTransform:"uppercase" }}>
              {ticket.device_brand}
            </span>
          </div>
          <div className="ticket-device-brand" style={{ fontFamily:"'Space Grotesk', monospace", color:"var(--accent)" }}>
            #{ticket.tracking_token?.slice(0,8) || ticket.id}
          </div>
        </div>
        <div
          className="ticket-badge"
          style={{ background: cfg.color + "22", color: cfg.color, border:`1px solid ${cfg.color}44`, flexShrink:0 }}
        >
          {cfg.icon === "📋" ? <ClipboardList size={14} style={{ marginRight: 6 }} /> : <span style={{ marginRight: 6, fontSize: 10, fontFamily: "monospace" }}>{cfg.icon}</span>}
          {cfg.label}
        </div>
      </div>

      {/* BODY: 2-column grid — CLIENTE | DETALLES */}
      <div className="ticket-card-body">
        {/* Col 1 — Cliente */}
        <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
          <span style={{ fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:"var(--text3)" }}>Cliente</span>
          <div className="ticket-meta-row">
            <span className="ticket-meta-icon"><User size={14} color="var(--text3)" /></span>
            <span className="ticket-meta-text" style={{ fontWeight:600 }}>
              {ticket.customer?.full_name || ticket._frontendName || ticket.client_email || "—"}
            </span>
          </div>
          {(ticket.customer?.phone_number || ticket._frontendPhone) && (
            <div className="ticket-meta-row">
              <span className="ticket-meta-icon"><Smartphone size={14} color="var(--text3)" /></span>
              <span className="ticket-meta-text">{ticket.customer?.phone_number || ticket._frontendPhone}</span>
            </div>
          )}
          <div className="ticket-meta-row">
            <span className="ticket-meta-icon"><Mail size={14} color="var(--text3)" /></span>
            <span className="ticket-meta-text">{ticket.client_email || ticket.customer?.email || "—"}</span>
          </div>
        </div>

        {/* Col 2 — Detalles */}
        <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
          <span style={{ fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:"var(--text3)" }}>Detalles</span>
          {ticket.issue_description && (
            <div className="ticket-meta-row" style={{ alignItems:"flex-start" }}>
              <span className="ticket-meta-icon"><AlertTriangle size={14} color="var(--text3)" /></span>
              <span className="ticket-meta-text">{ticket.issue_description}</span>
            </div>
          )}
          <div className="ticket-meta-row">
            <span className="ticket-meta-icon"><Calendar size={14} color="var(--text3)" /></span>
            <span className="ticket-meta-text">Ingreso: {formatDate(ticket.created_at)}</span>
          </div>
        </div>

        {/* METADATA ROW — spans full width, below both columns */}
        <div style={{ gridColumn:"1 / -1", display:"flex", alignItems:"center", gap:10, flexWrap:"wrap", padding:"10px 0 2px", borderTop:"1px solid var(--border)", marginTop:4 }}>
          {ticket.device_password && ticket.device_password.trim() !== ""
            ? <span style={{ display:"inline-flex", alignItems:"center", gap:4, fontSize:11, padding:"2px 8px", borderRadius:6, background:"rgba(201,167,106,0.08)", border:"1px solid rgba(201,167,106,0.25)", color:"var(--accent)" }}><Lock size={12} /> PIN cifrado</span>
            : <span style={{ fontSize:11, color:"var(--text3)" }}>Sin PIN</span>
          }
          <span style={{ display:"inline-flex", alignItems:"center", gap:4, fontSize:11, color: evidences.length > 0 ? "var(--accent)" : "var(--text3)" }}>
            <Paperclip size={12} /> {loadingEvidences ? "…" : `${evidences.length} evidencia${evidences.length !== 1 ? "s" : ""}`}
          </span>
          {ticket.diagnostic_notes
            ? <span style={{ display:"inline-flex", alignItems:"center", gap:4, fontSize:11, color:"var(--text2)", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap", maxWidth:220 }}><Wrench size={12} /> {ticket.diagnostic_notes}</span>
            : <span style={{ fontSize:11, color:"var(--text3)", fontStyle:"italic" }}>Sin diagnóstico</span>
          }
        </div>
      </div>

      {/* FOOTER: WhatsApp + status select + save button */}
      <div className="ticket-card-footer">
        {waPhone && (
          <a
            href={`https://wa.me/${waPhone}?text=${encodeURIComponent(`Hola ${ticket.customer?.full_name || ticket._frontendName || ""}, su equipo ${ticket.device_brand} ${ticket.device_model} fue ingresado. Siga su estado: ${window.location.origin}/tracking/${ticket.tracking_token}`)}`}
            target="_blank"
            rel="noreferrer"
            aria-label="Contactar por WhatsApp"
            style={{
              display:"inline-flex", alignItems:"center", gap:5,
              padding:"7px 12px", borderRadius:8, fontSize:12, fontWeight:600,
              background:"rgba(37,211,102,0.10)", border:"1px solid rgba(37,211,102,0.25)",
              color:"var(--whatsapp)", textDecoration:"none", flexShrink:0,
            }}
          >
            <MessageCircle size={14} /> WhatsApp
          </a>
        )}
        <select
          className="status-select"
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
        >
          {ADMIN_STATUSES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
        <button
          className="btn-save-status"
          onClick={handleSaveStatus}
          disabled={!isDirty || saving}
        >
          {saving ? "…" : "Guardar"}
        </button>
        <button
          onClick={() => setShowDetail(true)}
          aria-label="Ver detalles del equipo"
          style={{ marginLeft:"auto", fontSize:12, color:"var(--info)", background:"none", border:"none", cursor:"pointer", fontWeight:600, display:"flex", alignItems:"center", gap:4 }}
        >
          Ver detalle →
        </button>
      </div>

    </div>

    {showDetail && (
      <div 
        style={{ position:"fixed", inset:0, zIndex:1000, background:"rgba(0,0,0,0.75)", display:"flex", alignItems:"center", justifyContent:"center", padding:16 }}
        onClick={(e) => { if (e.target === e.currentTarget) closeDetail(); }}
        role="dialog"
        aria-modal="true"
        aria-label={`Detalles del equipo ${ticket.device_model}`}
      >
        <div style={{ background:"var(--surface)", border:"1px solid var(--border)", borderRadius:12, width:"100%", maxWidth:560, maxHeight:"90vh", overflowY:"auto", display:"flex", flexDirection:"column" }}>
          
          {/* Modal Header */}
          <div style={{ padding:"16px 20px", borderBottom:"1px solid var(--border)", display:"flex", justifyContent:"space-between", alignItems:"center", background:"var(--bg)", borderRadius:"12px 12px 0 0" }}>
            <div>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                <span style={{ fontSize:18, fontWeight:700, color:"var(--text1)" }}>{ticket.device_model}</span>
                <span style={{ fontSize:11, background:"var(--bg)", border:"1px solid var(--border)", color:"var(--text3)", padding:"1px 8px", borderRadius:4, fontWeight:700, textTransform:"uppercase" }}>{ticket.device_brand}</span>
              </div>
              <div style={{ fontSize:12, color:"var(--accent)", fontFamily:"'Space Grotesk', monospace", marginTop:2 }}>#{ticket.tracking_token || ticket.id}</div>
            </div>
            <button onClick={closeDetail} aria-label="Cerrar detalle" style={{ background:"none", border:"none", color:"var(--text3)", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center" }}>
              <X size={20} />
            </button>
          </div>

          {/* Modal Body */}
          <div style={{ padding:20, display:"flex", flexDirection:"column", gap:20 }}>

            {/* Section: Cliente */}
            <div>
              <div style={{ fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:"var(--text3)", marginBottom:10 }}>Datos del Cliente</div>
              <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                <div style={{ display:"flex", gap:8, fontSize:13, color:"var(--text2)", alignItems: "center" }}><User size={14} /><span style={{ fontWeight:600, color:"var(--text1)" }}>{ticket.customer?.full_name || ticket._frontendName || "—"}</span></div>
                {(ticket.customer?.phone_number || ticket._frontendPhone) && (
                  <div style={{ display:"flex", gap:8, fontSize:13, color:"var(--text2)", alignItems: "center" }}><Smartphone size={14} /><span>{ticket.customer?.phone_number || ticket._frontendPhone}</span></div>
                )}
                <div style={{ display:"flex", gap:8, fontSize:13, color:"var(--text2)", alignItems: "center" }}><Mail size={14} /><span>{ticket.client_email || ticket.customer?.email || "—"}</span></div>
              </div>
            </div>

            {/* Section: Dispositivo */}
            <div>
              <div style={{ fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:"var(--text3)", marginBottom:10 }}>Dispositivo</div>
              <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
                <div style={{ display:"flex", gap:8, fontSize:13, color:"var(--text2)", alignItems: "center" }}><Calendar size={14} /><span>Ingreso: {formatDate(ticket.created_at)}</span></div>
                {ticket.issue_description && (
                  <div style={{ fontSize:13, color:"var(--text2)", background:"var(--bg)", border:"1px solid var(--border)", borderRadius:6, padding:"10px 12px", display:"flex", gap:8 }}><AlertTriangle size={14} style={{flexShrink:0, marginTop:2}}/> {ticket.issue_description}</div>
                )}
                {ticket.device_password && ticket.device_password.trim() !== "" && (
                  <div style={{ display:"flex", gap:8, fontSize:13, alignItems:"center", color:"var(--text2)" }}>
                    <Lock size={14} />
                    <span style={{ fontFamily:"'Space Grotesk', monospace", color:"var(--accent)", fontWeight:600, background:"rgba(201,167,106,0.08)", border:"1px solid rgba(201,167,106,0.2)", padding:"2px 10px", borderRadius:4 }}>
                      {ticket.device_password}
                    </span>
                    <span style={{ fontSize:11, color:"var(--text3)" }}>PIN del dispositivo</span>
                  </div>
                )}
              </div>
            </div>

            {/* Section: Diagnóstico */}
            {(ticket.status === "EN_REVISION" || ticket.status === "ESPERANDO_APROBACION") && (
              <div>
                <div style={{ fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:"var(--text3)", marginBottom:10 }}>Diagnóstico y Presupuesto</div>
                {!showDiagForm && ticket.status === "EN_REVISION" && (
                  <button onClick={() => setShowDiagForm(true)} style={{ background:"rgba(201,167,106,0.10)", border:"1px solid rgba(201,167,106,0.22)", borderRadius:8, padding:"9px 16px", color:"var(--accent)", fontSize:13, fontWeight:600, cursor:"pointer", width:"100%", display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
                    <ClipboardList size={16} /> Enviar diagnóstico
                  </button>
                )}
                {(showDiagForm || ticket.status === "ESPERANDO_APROBACION") && (
                  <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
                    {diagError && <div style={{ fontSize:11, color:"var(--danger)", display:"flex", alignItems:"center", gap:4 }}><AlertTriangle size={12} /> {diagError}</div>}
                    <textarea className="form-textarea" placeholder="Describe el diagnóstico y las piezas a reemplazar..." value={diagNotes} onChange={(e) => { setDiagNotes(e.target.value); setDiagError(null); }} style={{ minHeight:80, fontSize:13 }} />
                    <input className="form-input" type="number" step="0.01" min="0" placeholder="Costo total (ej. 45.00)" value={diagCost} onChange={(e) => { setDiagCost(e.target.value); setDiagError(null); }} style={{ fontSize:13 }} />
                    <button className="btn-primary" onClick={handleSendDiagnostic} disabled={diagSaving || !diagNotes.trim() || !diagCost} style={{ padding:"10px 16px", fontSize:13 }}>
                      {diagSaving ? "Enviando…" : "Enviar presupuesto al cliente ✓"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Section: Evidencias */}
            <div>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:10 }}>
                <div style={{ fontSize:11, fontWeight:700, letterSpacing:"0.1em", textTransform:"uppercase", color:"var(--text3)" }}>Evidencias</div>
                <label style={{ background:"rgba(201,167,106,0.10)", border:"1px dashed rgba(201,167,106,0.35)", padding:"4px 10px", borderRadius:8, fontSize:11, color:"var(--accent)", cursor: uploading ? "not-allowed" : "pointer", fontWeight:500, display:"inline-flex", alignItems:"center", gap:6 }}>
                  {uploading ? <span className="spinner" style={{ width:12, height:12, borderWidth:1 }} /> : <Camera size={14} />}
                  {uploading ? "Subiendo..." : "Agregar evidencia"}
                  <input type="file" accept="image/jpeg, image/png, image/webp" style={{ display:"none" }} onChange={handleUploadEvidence} disabled={uploading} />
                </label>
              </div>
              {uploadError && <div style={{ fontSize:11, color:"var(--danger)", marginBottom:8, display:"flex", alignItems:"center", gap:4 }}><AlertTriangle size={12} /> {uploadError}</div>}
              {loadingEvidences ? (
                <div style={{ fontSize:12, color:"var(--text3)" }}>Cargando evidencias...</div>
              ) : evidences.length > 0 ? (
                <div style={{ display:"flex", gap:8, flexWrap:"wrap" }}>
                  {evidences.map(ev => (
                    <a key={ev.id} href={ev.file_url} target="_blank" rel="noreferrer">
                      <img src={ev.file_url} alt="evidencia" style={{ width:64, height:64, objectFit:"cover", borderRadius:8, border:"1px solid var(--border)" }} />
                    </a>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize:12, color:"var(--text3)", fontStyle:"italic" }}>Sin fotos subidas aún</div>
              )}
            </div>

          </div>
        </div>
      </div>
    )}
    </>
  );
}
