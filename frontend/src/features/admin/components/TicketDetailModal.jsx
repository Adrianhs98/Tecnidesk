import React, { useState, useEffect, useCallback, Suspense, lazy } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import imageCompression from "browser-image-compression";
import {
  User,
  Smartphone,
  Mail,
  AlertTriangle,
  Calendar,
  Lock,
  Wrench,
  ClipboardList,
  Camera,
  X,
  Eye,
  EyeOff
} from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { formatDate } from "../../../utils/date";
import { maskPhone, maskEmail } from "../../../utils/privacy";
import { formatCurrency } from "../../../utils/currency";
import PartsSelector from "./PartsSelector";

const DiagnosticModal = lazy(() => import("./DiagnosticModal"));

export default function TicketDetailModal({ ticket, onClose, onStatusChange }) {
  const [showPii, setShowPii] = useState(false);
  const [evidences, setEvidences] = useState([]);
  const [loadingEvidences, setLoadingEvidences] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [showDiagModal, setShowDiagModal] = useState(false);
  const [technicians, setTechnicians] = useState([]);

  const queryClient = useQueryClient();
  const { data: ticketDetails, isLoading: loadingItems } = useQuery({
    queryKey: ['ticketDetails', ticket.id],
    queryFn: async () => {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}`);
      if (!res.ok) throw new Error("Error fetching details");
      return res.json();
    },
    staleTime: 1000 * 60 * 5,
  });

  const items = ticketDetails?.items || [];
  const setItems = useCallback((updater) => {
    queryClient.setQueryData(['ticketDetails', ticket.id], (oldData) => {
      const currentItems = oldData?.items || [];
      const newItems = typeof updater === 'function' ? updater(currentItems) : updater;
      return { ...oldData, items: newItems };
    });
  }, [queryClient, ticket.id]);

  useEffect(() => {
    let mounted = true;
    authFetch(`${API_BASE}/technicians`)
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        if (mounted) setTechnicians(data);
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

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
    return () => {
      mounted = false;
    };
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
        initialQuality: 0.8,
      };
      const compressedFile = await imageCompression(file, options);

      const formData = new FormData();
      formData.append("file", compressedFile, compressedFile.name || "evidence.jpg");

      const token = sessionStorage.getItem("td_token");
      const res = await fetch(`${API_BASE}/tickets/${ticket.id}/evidences`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Error ${res.status}`);
      }

      const newEv = await res.json();
      setEvidences((prev) => [...prev, newEv]);
    } catch (err) {
      setUploadError(err.message || "Error al subir imagen");
    } finally {
      setUploading(false);
      e.target.value = null;
    }
  };

  const handleItemsUpdated = async () => {
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}`);
      if (res.ok) {
        const updated = await res.json();
        queryClient.setQueryData(['ticketDetails', ticket.id], updated);
        if (onStatusChange) onStatusChange(updated);
      }
    } catch (err) {
      console.error("Error refreshing ticket on items update:", err);
    }
  };

  const handleAssign = async (e) => {
    const newTechId = e.target.value;
    if (!newTechId) return;
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/assign`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ technician_id: newTechId }),
      });
      if (res.ok) {
        const updated = await res.json();
        if (onStatusChange) onStatusChange(updated);
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(errData.detail || "Error al reasignar técnico");
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDiagnosticSuccess = (updatedTicket) => {
    setShowDiagModal(false);
    if (onStatusChange) onStatusChange(updatedTicket);
    queryClient.invalidateQueries({ queryKey: ['ticketDetails', ticket.id] });
  };

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

  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 1000,
          background: "rgba(0,0,0,0.75)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 16,
        }}
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        role="dialog"
        aria-modal="true"
        aria-label={`Detalles del equipo ${ticket.device_model}`}
      >
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            width: "100%",
            maxWidth: 560,
            maxHeight: "90vh",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Modal Header */}
          <div
            style={{
              padding: "16px 20px",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: "var(--bg)",
              borderRadius: "12px 12px 0 0",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 18, fontWeight: 700, color: "var(--text1)" }}>
                  {ticket.device_model}
                </span>
                <span
                  style={{
                    fontSize: 11,
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    color: "var(--text3)",
                    padding: "1px 8px",
                    borderRadius: 4,
                    fontWeight: 700,
                    textTransform: "uppercase",
                  }}
                >
                  {ticket.device_brand}
                </span>
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: "var(--accent)",
                  fontFamily: "'Space Grotesk', monospace",
                  marginTop: 2,
                }}
              >
                #{ticket.tracking_token || ticket.id}
              </div>
            </div>
            <button
              onClick={onClose}
              aria-label="Cerrar detalle"
              style={{
                background: "none",
                border: "none",
                color: "var(--text3)",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <X size={20} />
            </button>
          </div>

          {/* Modal Body */}
          <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Section: Cliente */}
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 10,
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "var(--text3)",
                  }}
                >
                  Datos del Cliente
                </div>
                <button
                  type="button"
                  onClick={() => setShowPii(!showPii)}
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                    color: "var(--text2)",
                    fontSize: 11,
                  }}
                  title={showPii ? "Ocultar datos" : "Mostrar datos"}
                >
                  {showPii ? <EyeOff size={14} /> : <Eye size={14} />}
                  <span>{showPii ? "Ocultar" : "Ver"}</span>
                </button>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    fontSize: 13,
                    color: "var(--text2)",
                    alignItems: "center",
                  }}
                >
                  <User size={14} />
                  <span style={{ fontWeight: 600, color: "var(--text1)" }}>
                    {ticket.customer?.full_name || ticket._frontendName || "—"}
                  </span>
                </div>
                {(ticket.customer?.phone_number || ticket._frontendPhone) && (
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      fontSize: 13,
                      color: "var(--text2)",
                      alignItems: "center",
                    }}
                  >
                    <Smartphone size={14} />
                    <span>
                      {showPii
                        ? ticket.customer?.phone_number || ticket._frontendPhone
                        : maskPhone(ticket.customer?.phone_number || ticket._frontendPhone)}
                    </span>
                  </div>
                )}
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    fontSize: 13,
                    color: "var(--text2)",
                    alignItems: "center",
                  }}
                >
                  <Mail size={14} />
                  <span>
                    {showPii
                      ? ticket.client_email || ticket.customer?.email || "—"
                      : maskEmail(ticket.client_email || ticket.customer?.email || "—")}
                  </span>
                </div>
              </div>
            </div>

            {/* Section: Dispositivo */}
            <div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  color: "var(--text3)",
                  marginBottom: 10,
                }}
              >
                Dispositivo
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    fontSize: 13,
                    color: "var(--text2)",
                    alignItems: "center",
                  }}
                >
                  <Calendar size={14} />
                  <span>Ingreso: {formatDate(ticket.created_at)}</span>
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    fontSize: 13,
                    color: "var(--text2)",
                    alignItems: "center",
                  }}
                >
                  <Wrench size={14} />
                  <span>Técnico:</span>
                  <select
                    value={ticket.technician?.id || ""}
                    onChange={handleAssign}
                    style={{
                      background: "var(--surface2)",
                      color: "var(--text1)",
                      border: "1px solid var(--border)",
                      borderRadius: "6px",
                      padding: "4px 8px",
                      fontSize: "12px",
                    }}
                  >
                    <option value="" disabled>
                      Sin asignar
                    </option>
                    {technicians.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.full_name}
                      </option>
                    ))}
                  </select>
                </div>
                {ticket.issue_description && (
                  <div
                    style={{
                      fontSize: 13,
                      color: "var(--text2)",
                      background: "var(--bg)",
                      border: "1px solid var(--border)",
                      borderRadius: 6,
                      padding: "10px 12px",
                      display: "flex",
                      gap: 8,
                    }}
                  >
                    <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 2 }} />{" "}
                    {ticket.issue_description}
                  </div>
                )}
                {ticket.device_password && ticket.device_password.trim() !== "" && (
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      fontSize: 13,
                      alignItems: "center",
                      color: "var(--text2)",
                    }}
                  >
                    <Lock size={14} />
                    <span
                      style={{
                        fontFamily: "'Space Grotesk', monospace",
                        color: "var(--accent)",
                        fontWeight: 600,
                        background: "rgba(201,167,106,0.08)",
                        border: "1px solid rgba(201,167,106,0.2)",
                        padding: "2px 10px",
                        borderRadius: 4,
                      }}
                    >
                      {ticket.device_password}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text3)" }}>PIN del dispositivo</span>
                  </div>
                )}
              </div>
            </div>

            {/* Section: Diagnóstico y Presupuesto */}
            <div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  color: "var(--text3)",
                  marginBottom: 10,
                }}
              >
                Diagnóstico y Presupuesto
              </div>

              {ticket.status === "EN_REVISION" && (
                <button
                  onClick={() => setShowDiagModal(true)}
                  style={{
                    background: "rgba(201,167,106,0.10)",
                    border: "1px solid rgba(201,167,106,0.22)",
                    borderRadius: 8,
                    padding: "9px 16px",
                    color: "var(--accent)",
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    marginBottom: 12,
                  }}
                >
                  <ClipboardList size={16} />
                  {ticket.diagnostic_notes ? "Actualizar diagnóstico" : "Escribir diagnóstico"}
                </button>
              )}

              {ticket.diagnostic_notes && (
                <div
                  style={{
                    fontSize: 13,
                    color: "var(--text2)",
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    padding: "10px 12px",
                    marginBottom: 12,
                  }}
                >
                  <span
                    style={{
                      fontWeight: 600,
                      display: "block",
                      fontSize: 11,
                      color: "var(--text3)",
                      textTransform: "uppercase",
                      marginBottom: 4,
                    }}
                  >
                    Diagnóstico:
                  </span>
                  {ticket.diagnostic_notes}
                </div>
              )}

              {loadingItems ? (
                <div style={{ fontSize: 12, color: "var(--text3)" }}>Cargando...</div>
              ) : (
                <PartsSelector
                  ticketId={ticket.id}
                  items={items}
                  setItems={setItems}
                  status={ticket.status}
                  onItemsUpdated={handleItemsUpdated}
                />
              )}

              <div
                style={{
                  padding: 12,
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginTop: 12,
                }}
              >
                <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text2)" }}>
                  Costo Total:
                </span>
                <span
                  style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: "var(--success)",
                    fontFamily: "monospace",
                  }}
                >
                  {formatCurrency(ticket.total_cost || 0)}
                </span>
              </div>
            </div>

            {/* Section: Evidencias */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 10,
                }}
              >
                <div
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    textTransform: "uppercase",
                    color: "var(--text3)",
                  }}
                >
                  Evidencias
                </div>
                <label
                  style={{
                    background: "rgba(201,167,106,0.10)",
                    border: "1px dashed rgba(201,167,106,0.35)",
                    padding: "4px 10px",
                    borderRadius: 8,
                    fontSize: 11,
                    color: "var(--accent)",
                    cursor: uploading ? "not-allowed" : "pointer",
                    fontWeight: 500,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  {uploading ? (
                    <span className="spinner" style={{ width: 12, height: 12, borderWidth: 1 }} />
                  ) : (
                    <Camera size={14} />
                  )}
                  {uploading ? "Subiendo..." : "Agregar evidencia"}
                  <input
                    type="file"
                    accept="image/jpeg, image/png, image/webp"
                    style={{ display: "none" }}
                    onChange={handleUploadEvidence}
                    disabled={uploading}
                  />
                </label>
              </div>
              {uploadError && (
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--danger)",
                    marginBottom: 8,
                    display: "flex",
                    alignItems: "center",
                    gap: 4,
                  }}
                >
                  <AlertTriangle size={12} /> {uploadError}
                </div>
              )}
              {loadingEvidences ? (
                <div style={{ fontSize: 12, color: "var(--text3)" }}>Cargando evidencias...</div>
              ) : evidences.length > 0 ? (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {evidences.map((ev) => (
                    <a key={ev.id} href={ev.file_url} target="_blank" rel="noreferrer">
                      <img
                        src={ev.file_url}
                        alt="evidencia"
                        style={{
                          width: 64,
                          height: 64,
                          objectFit: "cover",
                          borderRadius: 8,
                          border: "1px solid var(--border)",
                        }}
                      />
                    </a>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "var(--text3)", fontStyle: "italic" }}>
                  Sin fotos subidas aún
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <Suspense fallback={<div className="modal-overlay"><div className="spinner" /></div>}>
        {showDiagModal && (
          <DiagnosticModal
            ticketId={ticket.id}
            ticket={ticket}
            onClose={() => setShowDiagModal(false)}
            onSuccess={handleDiagnosticSuccess}
          />
        )}
      </Suspense>
    </>
  );
}
