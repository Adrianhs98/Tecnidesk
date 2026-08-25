import { useState, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import imageCompression from "browser-image-compression";
import {
  X,
  Smartphone,
  Lock,
  Unlock,
  KeyRound,
  Wrench,
  Camera,
  Bot,
  Sparkles,
  CheckCircle2,
  Clock,
  User,
  AlertTriangle,
  FileText,
  Package,
  Save,
  Eye,
  EyeOff,
} from "lucide-react";
import { authFetch } from "../../api/authFetch";
import { API_BASE } from "../../api/config";
import { revealTicketPin } from "../../api/technician";
import { maskPhone } from "../../utils/privacy";
import PartsSelector from "../admin/components/PartsSelector";

const QUICK_STATUSES = [
  { key: "EN_REVISION", label: "En Revisión", icon: "🔍", color: "#B89251" },
  { key: "ESPERANDO_REPUESTO", label: "Esperando Repuesto", icon: "📦", color: "#6F9FCC" },
  { key: "EN_REPARACION", label: "En Reparación", icon: "⚙️", color: "#6F9FCC" },
  { key: "LISTO_PARA_RETIRAR", label: "Listo para Retirar", icon: "✅", color: "var(--success)" },
];

export default function TechnicianWorkModal({
  ticket,
  onClose,
  onStatusChange,
  onOpenAiCopilot,
  isReadOnly = false,
}) {
  const queryClient = useQueryClient();

  const [revealedPin, setRevealedPin] = useState(null);
  const [isPinMasked, setIsPinMasked] = useState(true);
  const [loadingPin, setLoadingPin] = useState(false);
  const [pinError, setPinError] = useState(null);

  const [diagnosticNotes, setDiagnosticNotes] = useState(ticket?.diagnostic_notes || "");
  const [savingNotes, setSavingNotes] = useState(false);
  const [notesSuccess, setNotesSuccess] = useState(false);

  const [evidences, setEvidences] = useState([]);
  const [loadingEvidences, setLoadingEvidences] = useState(false);
  const [uploadingEvidence, setUploadingEvidence] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const [statusUpdating, setStatusUpdating] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(ticket?.status);

  // Query ticket details for items/parts
  const { data: ticketDetails } = useQuery({
    queryKey: ["ticketDetails", ticket.id],
    queryFn: async () => {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}`);
      if (!res.ok) throw new Error("Error cargando detalles");
      return res.json();
    },
    staleTime: 1000 * 60 * 5,
  });

  const items = ticketDetails?.items || [];
  const setItems = useCallback(
    (updater) => {
      queryClient.setQueryData(["ticketDetails", ticket.id], (oldData) => {
        const currentItems = oldData?.items || [];
        const newItems = typeof updater === "function" ? updater(currentItems) : updater;
        return { ...oldData, items: newItems };
      });
    },
    [queryClient, ticket.id]
  );

  // Fetch evidences
  useEffect(() => {
    let isMounted = true;
    const fetchEvidences = async () => {
      setLoadingEvidences(true);
      try {
        const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/evidences`);
        if (res.ok && isMounted) {
          const data = await res.json();
          setEvidences(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error("Error fetching evidences:", err);
      } finally {
        if (isMounted) setLoadingEvidences(false);
      }
    };
    fetchEvidences();
    return () => {
      isMounted = false;
    };
  }, [ticket.id]);

  // Escape key handler
  useEffect(() => {
    document.body.style.overflow = "hidden";
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = "unset";
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  // Handle Reveal PIN
  const handleRevealPin = async () => {
    setLoadingPin(true);
    setPinError(null);
    try {
      const data = await revealTicketPin(ticket.id);
      setRevealedPin(data.device_password || data.pin || "Sin PIN registrado");
      setIsPinMasked(true);
    } catch (err) {
      setPinError(err.message || "No se pudo revelar el PIN");
    } finally {
      setLoadingPin(false);
    }
  };

  // Quick Status Transition (1-Click)
  const handleQuickStatus = async (newStatus) => {
    if (newStatus === currentStatus) return;
    setStatusUpdating(true);
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Error al actualizar estado");
      }

      const updated = await res.json();
      setCurrentStatus(newStatus);
      if (onStatusChange) {
        onStatusChange(updated);
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setStatusUpdating(false);
    }
  };

  // Save diagnostic notes
  const handleSaveNotes = async () => {
    setSavingNotes(true);
    setNotesSuccess(false);
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diagnostic_notes: diagnosticNotes }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Error al guardar notas");
      }

      const updated = await res.json();
      setNotesSuccess(true);
      if (onStatusChange) onStatusChange(updated);
      setTimeout(() => setNotesSuccess(false), 2500);
    } catch (err) {
      alert(err.message);
    } finally {
      setSavingNotes(false);
    }
  };

  // Upload photographic evidence
  const handleUploadEvidence = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    setUploadingEvidence(true);

    try {
      const options = {
        maxSizeMB: 0.8,
        maxWidthOrHeight: 1200,
        useWebWorker: true,
      };
      const compressedFile = await imageCompression(file, options);
      const formData = new FormData();
      formData.append("file", compressedFile, file.name);

      const token = sessionStorage.getItem("td_token");
      const res = await fetch(`${API_BASE}/tickets/${ticket.id}/evidences`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Error al subir evidencia");
      }

      const newEvidence = await res.json();
      setEvidences((prev) => [newEvidence, ...prev]);
    } catch (err) {
      setUploadError(err.message || "Error al comprimir o subir imagen");
    } finally {
      setUploadingEvidence(false);
      e.target.value = "";
    }
  };

  const customerName = ticket.customer?.full_name || ticket.customer_name || "Cliente";
  const customerPhone = ticket.customer?.phone_number || ticket.customer_phone;
  const maskedPhone = customerPhone ? maskPhone(customerPhone) : null;

  return (
    <div
      className="tech-modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label={`Mesa de trabajo para ${ticket.device_brand} ${ticket.device_model}`}
    >
      <div className="tech-work-modal">
        {/* Modal Header */}
        <header className="tech-modal-header">
          <div className="tech-modal-title-group">
            <div className="tech-modal-device-badge">
              <Smartphone size={20} />
              <h2>
                {ticket.device_brand} {ticket.device_model}
              </h2>
            </div>
            <span className="mono tech-modal-tracking-pill">
              #{ticket.tracking_token || ticket.id}
            </span>
          </div>

          <div className="tech-modal-header-actions">
            {!isReadOnly && (
              <button
                type="button"
                className="btn-primary tech-copilot-cta-btn"
                onClick={() => onOpenAiCopilot?.(ticket)}
                data-testid="open-ai-copilot-ticket-btn"
              >
                <Sparkles size={16} />
                <span>Ohm</span>
              </button>
            )}
            <button
              type="button"
              className="tech-modal-close-btn"
              onClick={onClose}
              aria-label="Cerrar modal de trabajo"
            >
              <X size={20} />
            </button>
          </div>
        </header>

        {/* Modal Scrollable Content */}
        <div className="tech-modal-content">
          {/* Quick Status Bar */}
          <section className="tech-section tech-status-section">
            <div className="tech-section-header-row">
              <label className="tech-section-label">
                <Clock size={15} />
                <span>Estado de Reparación (Cambio en 1-Clic)</span>
              </label>
              {isReadOnly && (
                <span className="tech-readonly-indicator" data-testid="supervisor-readonly-indicator">
                  Modo Supervisor: solo lectura
                </span>
              )}
            </div>
            <div className="tech-quick-status-grid">
              {QUICK_STATUSES.map((st) => {
                const isActive = currentStatus === st.key;
                return (
                  <button
                    key={st.key}
                    type="button"
                    className={`tech-status-btn ${isActive ? "active" : ""}`}
                    onClick={() => handleQuickStatus(st.key)}
                    disabled={statusUpdating || isReadOnly}
                    data-testid={`quick-status-${st.key}`}
                  >
                    <span className="tech-status-btn-icon">{st.icon}</span>
                    <span className="tech-status-btn-label">{st.label}</span>
                    {isActive && <CheckCircle2 size={14} className="tech-status-check" />}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Grid: Device Info & PIN Security */}
          <div className="tech-grid-2col">
            {/* Left: Device & Customer Info */}
            <section className="tech-section tech-info-box">
              <label className="tech-section-label">
                <AlertTriangle size={15} />
                <span>Falla Reportada & Cliente</span>
              </label>
              <div className="tech-issue-banner">
                <strong>Falla del cliente:</strong>
                <p>{ticket.issue_description || "Sin descripción específica registrada."}</p>
              </div>
              <div className="tech-customer-snippet">
                <User size={14} />
                <span>{customerName}</span>
                {maskedPhone && <span className="mono text-muted">({maskedPhone})</span>}
              </div>
            </section>

            {/* Right: Reveal PIN Security Vault */}
            <section className="tech-section tech-pin-vault" data-testid="pin-reveal-section">
              <label className="tech-section-label">
                <KeyRound size={15} />
                <span>PIN / Patrón de Desbloqueo</span>
              </label>
              <div className="tech-pin-content">
                {revealedPin ? (
                  <div className="tech-pin-revealed-box" data-testid="revealed-pin-display">
                    <div className="tech-pin-val-wrap">
                      <Unlock size={18} className="pin-unlock-icon" />
                      <span className="mono tech-pin-number" data-testid="revealed-pin-text">
                        {isPinMasked ? "••••••••" : revealedPin}
                      </span>
                      <button
                        type="button"
                        className="tech-pin-toggle-btn"
                        onClick={() => setIsPinMasked((prev) => !prev)}
                        title={isPinMasked ? "Mostrar PIN" : "Ocultar PIN"}
                        aria-label={isPinMasked ? "Mostrar PIN" : "Ocultar PIN"}
                        data-testid="toggle-pin-mask-btn"
                      >
                        {isPinMasked ? <Eye size={16} /> : <EyeOff size={16} />}
                      </button>
                    </div>
                    <span className="tech-pin-audit-note">
                      🔒 PIN auditado y registrado en historial de seguridad
                    </span>
                  </div>
                ) : isReadOnly ? (
                  <div className="tech-pin-masked-box">
                    <div className="tech-pin-placeholder">
                      <Lock size={16} />
                      <span>PIN Protegido (Modo Supervisor: solo lectura)</span>
                    </div>
                  </div>
                ) : (
                  <div className="tech-pin-masked-box">
                    <div className="tech-pin-placeholder">
                      <Lock size={16} />
                      <span>PIN Protegido</span>
                    </div>
                    <button
                      type="button"
                      className="btn-secondary tech-reveal-btn"
                      onClick={handleRevealPin}
                      disabled={loadingPin}
                      data-testid="reveal-pin-btn"
                    >
                      {loadingPin ? "Desencriptando..." : "Revelar PIN (Auditar)"}
                    </button>
                  </div>
                )}
                {pinError && <div className="tech-pin-error">{pinError}</div>}
              </div>
            </section>
          </div>

          {/* Diagnostic & Technical Notes */}
          <section className="tech-section">
            <div className="tech-section-header-row">
              <label className="tech-section-label">
                <FileText size={15} />
                <span>Diagnóstico y Notas Técnicas</span>
              </label>
              {!isReadOnly && (
                <button
                  type="button"
                  className="btn-secondary tech-save-notes-btn"
                  onClick={handleSaveNotes}
                  disabled={savingNotes}
                  data-testid="save-notes-btn"
                >
                  <Save size={14} />
                  <span>{savingNotes ? "Guardando..." : "Guardar Notas"}</span>
                </button>
              )}
            </div>
            {notesSuccess && (
              <div className="tech-success-banner">✓ Notas técnicas actualizadas</div>
            )}
            <textarea
              className="form-input tech-notes-textarea"
              rows={4}
              value={diagnosticNotes}
              onChange={(e) => setDiagnosticNotes(e.target.value)}
              placeholder="Escribe el diagnóstico técnico, mediciones en placa o componentes revisados..."
              disabled={isReadOnly}
              readOnly={isReadOnly}
              data-testid="diagnostic-notes-input"
            />
          </section>

          {/* Parts & Inventory Selector */}
          <section className="tech-section">
            <label className="tech-section-label">
              <Package size={15} />
              <span>Piezas y Repuestos Utilizados</span>
            </label>
            <div className="tech-parts-container">
              <PartsSelector
                ticketId={ticket.id}
                items={items}
                setItems={setItems}
                totalCost={ticket.total_cost}
              />
            </div>
          </section>

          {/* Photographic Evidences */}
          <section className="tech-section">
            <div className="tech-section-header-row">
              <label className="tech-section-label">
                <Camera size={15} />
                <span>Evidencias Fotográficas ({evidences.length})</span>
              </label>
              <label className="btn-secondary tech-upload-label">
                <Camera size={14} />
                <span>{uploadingEvidence ? "Subiendo..." : "Agregar Foto"}</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleUploadEvidence}
                  disabled={uploadingEvidence}
                  style={{ display: "none" }}
                  data-testid="evidence-file-input"
                />
              </label>
            </div>

            {uploadError && <div className="tech-pin-error">{uploadError}</div>}

            {loadingEvidences ? (
              <div className="tech-loading-text">Cargando evidencias...</div>
            ) : evidences.length === 0 ? (
              <div className="tech-empty-evidences">
                <Camera size={24} className="text-muted" />
                <p>No hay fotos o evidencias adjuntas a este equipo.</p>
              </div>
            ) : (
              <div className="tech-evidence-grid">
                {evidences.map((ev) => (
                  <div key={ev.id} className="tech-evidence-item">
                    <img
                      src={ev.file_url || `${API_BASE}/evidences/${ev.id}/file`}
                      alt={ev.file_name || "Evidencia"}
                      className="tech-evidence-thumb"
                      loading="lazy"
                    />
                    <span className="tech-evidence-desc" title={ev.file_name}>
                      {ev.file_name || "Foto"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
