import { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import LogoBadge from "../components/shared/LogoBadge";
import SkeletonCard from "../components/shared/SkeletonCard";
import Stepper from "../components/shared/Stepper";
import ThemeToggle from "../components/shared/ThemeToggle";
import { API_BASE } from "../api/config";
import { STATUS_CONFIG } from "../utils/constants";
import { formatDate } from "../utils/date";

export default function TrackingPortal() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [actionError, setActionError] = useState(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    setActionError(null);
    try {
      const res = await fetch(`${API_BASE}/tracking/${token}`);
      if (res.status === 404) {
        setError("No encontramos un ticket con ese codigo. Verifica que el enlace sea correcto.");
      } else if (!res.ok) {
        setError("Ocurrio un error al consultar. Intenta de nuevo mas tarde.");
      } else {
        setData(await res.json());
      }
    } catch {
      setError("No se pudo conectar con el servidor. Verifica tu conexion a internet.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [token]);

  const cfg = data ? STATUS_CONFIG[data.status] || { label: data.status_label || data.status, color: "#C9A76A", icon: "INFO" } : null;

  const handleApprove = async () => {
    setApproving(true);
    setActionError(null);
    try {
      const res = await fetch(`${API_BASE}/tracking/${token}/approve`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}: No se pudo procesar la aprobacion.`);
      }
      setData(await res.json());
    } catch (err) {
      setActionError(err.message || "Error al conectar con el servidor. Reintenta mas tarde.");
    } finally {
      setApproving(false);
    }
  };

  const handleReject = async () => {
    setRejecting(true);
    setActionError(null);
    try {
      const res = await fetch(`${API_BASE}/tracking/${token}/reject`, { method: "POST" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}: No se pudo procesar el rechazo.`);
      }
      setData(await res.json());
    } catch (err) {
      setActionError(err.message || "Error al conectar con el servidor. Reintenta mas tarde.");
    } finally {
      setRejecting(false);
    }
  };

  return (
    <div className="portal">
      <div className="header" style={{ paddingBottom: 16, position: "relative" }}>
        <div style={{ position: "absolute", top: 0, right: 0 }}>
          <ThemeToggle />
        </div>
        <LogoBadge 
          businessName={data?.shop_name} 
          logoUrl={data?.shop_logo_url} 
        />
      </div>

      <div style={{ width: "100%", maxWidth: 680, marginBottom: 12 }}>
        <button className="back-btn" onClick={() => navigate("/")}>
          Buscar otro equipo
        </button>
      </div>

      {loading && <SkeletonCard />}

      {!loading && error && (
        <>
          <div className="error-card">
            <span style={{ fontSize: 20 }}>ERROR</span>
            <span>{error}</span>
          </div>
          <button className="back-btn" style={{ marginTop: 12 }} onClick={() => navigate("/")}>
            Volver a buscar
          </button>
        </>
      )}

      {!loading && data && (
        <div className="result-card">
          <div className="result-header">
            <div>
              <div className="device-model">{data.device_model}</div>
              <div className="device-brand">{data.device_brand}</div>
            </div>
            <div className="status-badge" style={{ background: cfg.color + "22", color: cfg.color, border: `1px solid ${cfg.color}44` }}>
              {cfg.icon} {data.status_label || cfg.label}
            </div>
          </div>

          <Stepper status={data.status} />

          {data.status === "ESPERANDO_APROBACION" && (
            <div className="approval-wrap">
              <div className="approval-banner">
                <span style={{ fontSize: 22 }}>INFO</span>
                <div className="approval-text">
                  <strong>Tu aprobacion es necesaria.</strong> El tecnico reviso tu equipo y esta esperando tu confirmacion para proceder con la reparacion.
                </div>
              </div>

              {actionError && (
                <div className="admin-error-bar" style={{ marginTop: 12 }}>
                  <span>ERROR</span> {actionError}
                </div>
              )}

              <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap" }}>
                <button
                  onClick={handleApprove}
                  disabled={approving || rejecting}
                  style={{ flex: 1, minWidth: 140, padding: "12px 20px", borderRadius: 12, border: "none", background: "var(--success)", color: "#fff", fontFamily: "'DM Sans', sans-serif", fontSize: 14, fontWeight: 600, cursor: approving ? "not-allowed" : "pointer", opacity: approving ? 0.6 : 1, transition: "opacity 0.2s, background-color 0.2s" }}
                >
                  {approving ? "Procesando..." : "Aceptar presupuesto"}
                </button>
                <button
                  onClick={handleReject}
                  disabled={approving || rejecting}
                  style={{ flex: 1, minWidth: 140, padding: "12px 20px", borderRadius: 12, background: "transparent", border: "1px solid rgba(157,92,82,0.30)", color: "var(--danger)", fontFamily: "'DM Sans', sans-serif", fontSize: 14, fontWeight: 600, cursor: rejecting ? "not-allowed" : "pointer", opacity: rejecting ? 0.6 : 1, transition: "opacity 0.2s, background-color 0.2s" }}
                >
                  {rejecting ? "Procesando..." : "No aceptar"}
                </button>
              </div>

              {data.contact_whatsapp && data.total_cost && (
                <div style={{ marginTop: 16, textAlign: "center" }}>
                  <div style={{ fontSize: 13, color: "var(--text2)", marginBottom: 8 }}>
                    ¿Tienes alguna duda o inconveniente con este presupuesto? Contáctanos por WhatsApp.
                  </div>
                  <a
                    href={`https://wa.me/${data.contact_whatsapp}?text=${encodeURIComponent(`Hola, sobre mi equipo ${data.device_brand} ${data.device_model} (código: ${data.tracking_token || token}). Quisiera conversar sobre el presupuesto estimado de $${data.total_cost}.`)}`}
                    target="_blank"
                    rel="noreferrer"
                    style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "11px 20px", borderRadius: 12, background: "rgba(37,211,102,0.12)", border: "1px solid rgba(37,211,102,0.25)", color: "var(--whatsapp)", textDecoration: "none", fontFamily: "'DM Sans', sans-serif", fontSize: 13, fontWeight: 600, transition: "background-color 0.2s, transform 0.2s" }}
                  >
                    <MessageCircle size={14} /> Contactar al Taller
                  </a>
                </div>
              )}
            </div>
          )}

          {data.requires_approval && data.status !== "ESPERANDO_APROBACION" && (
            <div className="approval-wrap">
              <div className="approval-banner">
                <span style={{ fontSize: 22 }}>OK</span>
                <div className="approval-text">
                  <strong>Tu aprobacion fue registrada.</strong> Gracias por responder.
                </div>
              </div>
            </div>
          )}

          <div className="info-grid" style={{ marginTop: data.requires_approval ? 16 : 0 }}>
            <div className="info-tile full">
              <div className="tile-label">Problema reportado</div>
              <div className="tile-value">{data.issue_description}</div>
            </div>
            <div className="info-tile full">
              <div className="tile-label">Diagnostico tecnico</div>
              <div className={`tile-value ${!data.diagnostic_notes ? "empty" : ""}`}>{data.diagnostic_notes || "Pendiente de revision"}</div>
            </div>
            <div className="info-tile">
              <div className="tile-label">Presupuesto estimado</div>
              {data.total_cost ? <div className="tile-value cost">${parseFloat(data.total_cost).toFixed(2)}</div> : <div className="tile-value cost-pending">En evaluacion</div>}
            </div>
            <div className="info-tile">
              <div className="tile-label">Estado actual</div>
              <div className="tile-value" style={{ color: cfg.color, fontWeight: 600 }}>
                {data.status_label || cfg.label}
              </div>
            </div>
          </div>

          {data.evidences && data.evidences.length > 0 && (
            <div style={{ marginTop: 16, padding: "12px 16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)", borderRadius: 8 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text1)", marginBottom: 10 }}>Fotos del equipo</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {data.evidences.map((ev) => (
                  <a key={ev.id} href={ev.file_url} target="_blank" rel="noreferrer" title={ev.file_name}>
                    <img src={ev.file_url} alt={ev.file_name} style={{ width: 64, height: 64, objectFit: "cover", borderRadius: 8, border: "1px solid var(--border)", cursor: "pointer", transition: "transform 0.2s" }} onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.08)")} onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")} />
                  </a>
                ))}
              </div>
            </div>
          )}



          <div className="result-footer">
            <div>
              <div className="timestamp">
                Ingresado: <span>{formatDate(data.created_at)}</span>
              </div>
              <div className="timestamp" style={{ marginTop: 4 }}>
                Actualizado: <span>{formatDate(data.updated_at)}</span>
              </div>
            </div>
            <button className="refresh-btn" onClick={fetchStatus}>
              Actualizar
            </button>
          </div>
        </div>
      )}

      <div className="powered" style={{ marginTop: 24 }}>
        {data?.shop_name || "Portal de Rastreo"} | Impulsado por <span>TecniDesk</span>
      </div>
    </div>
  );
}
