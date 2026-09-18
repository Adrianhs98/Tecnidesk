import { useState, useEffect, Suspense, lazy } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { 
  AlertTriangle, 
  Wrench, 
  ClipboardList, 
  MessageCircle, 
  Eye, 
  Clock, 
  PackageCheck,
  Hourglass 
} from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { STATUS_CONFIG, ADMIN_STATUSES } from "../../../utils/constants";
import { formatRelativeAge, isTicketStale } from "../../../utils/date";
import { maskTrackingCode } from "../../../utils/privacy";
import StatusBadge from "../../../components/shared/StatusBadge";
import TicketDetailModal from "./TicketDetailModal";

const DiagnosticModal = lazy(() => import("./DiagnosticModal"));

export default function AdminTicketCard({ ticket, onStatusChange, slaThresholds = null }) {
  const cfg = STATUS_CONFIG[ticket.status] || { label: ticket.status, color: "var(--accent)", icon: "📋" };
  const stale = isTicketStale(ticket.updated_at || ticket.created_at, ticket.status, slaThresholds);
  const [selectedStatus, setSelectedStatus] = useState(ticket.status);
  const [saving, setSaving] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [showDiagModal, setShowDiagModal] = useState(false);

  const queryClient = useQueryClient();

  useEffect(() => {
    setSelectedStatus(ticket.status);
  }, [ticket.status]);

  const isDirty = selectedStatus !== ticket.status;

  const handleSaveStatus = async () => {
    if (!isDirty) return;
    setSaving(true);
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: selectedStatus }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Error ${res.status}`);
      }
      const updated = await res.json();
      if (onStatusChange) {
        onStatusChange(updated);
      }
    } catch (err) {
      alert(err.message || "Error al actualizar estado");
      setSelectedStatus(ticket.status);
    } finally {
      setSaving(false);
    }
  };

  const handleDiagnosticSuccess = (updatedTicket) => {
    setShowDiagModal(false);
    if (onStatusChange) {
      onStatusChange(updatedTicket);
    }
    queryClient.invalidateQueries({ queryKey: ['ticketDetails', ticket.id] });
  };

  const rawPhone = ticket.customer?.phone_number || ticket._frontendPhone || "";
  const cleanPhone = rawPhone.replace(/\D/g, "").replace(/^0/, "");
  const waPhone = cleanPhone ? "593" + cleanPhone : "";

  const renderExceptionBadges = () => {
    const badges = [];

    if (ticket.status === "EN_REVISION" && !ticket.diagnostic_notes) {
      badges.push(
        <span key="no-diag" className="badge-exception badge-muted">
          <Wrench size={12} /> Sin diagnóstico
        </span>
      );
    }

    if (stale) {
      badges.push(
        <span
          key="stale"
          className="badge-exception badge-danger"
          data-testid="sla-stale-badge"
          title="Tiempo límite de atención superado (SLA vencido)"
        >
          <Clock size={12} /> Vencido
        </span>
      );
    }

    if (ticket.status === "LISTO_PARA_RETIRAR") {
      badges.push(
        <span key="ready" className="badge-exception badge-success">
          <PackageCheck size={12} /> Listo p/ retiro
        </span>
      );
    }

    if (ticket.status === "ESPERANDO_APROBACION") {
      badges.push(
        <span key="approval" className="badge-exception badge-amber">
          <Hourglass size={12} /> Esperando aprobación
        </span>
      );
    }

    return badges;
  };

  const renderSmartAction = () => {
    // 1. Priority 1: No technician assigned -> Direct assign trigger
    if (!ticket.technician) {
      return (
        <button 
          className="btn-smart-action btn-smart-warning" 
          onClick={() => setShowDetail(true)}
          aria-label="Asignar técnico"
        >
          <Wrench size={14} /> Asignar
        </button>
      );
    }

    // 2. Priority 2: In revision without diagnosis -> Direct diagnostic modal trigger
    if (ticket.status === "EN_REVISION" && !ticket.diagnostic_notes) {
      return (
        <button 
          className="btn-smart-action btn-smart-accent" 
          onClick={() => setShowDiagModal(true)}
          aria-label="Diagnosticar equipo"
        >
          <ClipboardList size={14} /> Diagnosticar
        </button>
      );
    }

    // 3. Priority 3: Ready for pickup -> WhatsApp notification
    if (ticket.status === "LISTO_PARA_RETIRAR" && waPhone) {
      return (
        <a
          href={`https://wa.me/${waPhone}?text=${encodeURIComponent(
            `Hola ${ticket.customer?.full_name || ticket._frontendName || ""}, su equipo ${ticket.device_brand} ${ticket.device_model} (#${ticket.tracking_token || ticket.id}) está listo para ser retirado.`
          )}`}
          target="_blank"
          rel="noreferrer"
          className="btn-smart-action btn-smart-success"
          aria-label="WhatsApp: Retiro"
        >
          <MessageCircle size={14} /> WhatsApp: Retiro
        </a>
      );
    }

    // 4. Priority 4: Waiting approval -> WhatsApp quote follow-up
    if (ticket.status === "ESPERANDO_APROBACION" && waPhone) {
      return (
        <a
          href={`https://wa.me/${waPhone}?text=${encodeURIComponent(
            `Hola ${ticket.customer?.full_name || ticket._frontendName || ""}, le recordamos que el presupuesto de su equipo ${ticket.device_brand} ${ticket.device_model} está disponible para su aprobación: ${window.location.origin}/tracking/${ticket.tracking_token || ticket.id}`
          )}`}
          target="_blank"
          rel="noreferrer"
          className="btn-smart-action btn-smart-amber"
          aria-label="WhatsApp: Seguimiento"
        >
          <MessageCircle size={14} /> WhatsApp: Seguimiento
        </a>
      );
    }

    // Default: Standard detail button
    return (
      <button 
        className="btn-smart-action btn-smart-secondary" 
        onClick={() => setShowDetail(true)}
        aria-label="Ver detalle"
      >
        <Eye size={14} /> Ver detalle
      </button>
    );
  };

  return (
    <>
    <div className={`ticket-card workbench-card ${stale ? "is-stale" : ""}`} data-testid={`admin-ticket-card-${ticket.id}`}>

      {/* HEADER: device name, brand badge, tracking, client name, relative age, status badge */}
      <div className="ticket-card-header">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2, minWidth: 0 }}>
            <span className="ticket-device-name font-bold text-base text-[var(--text1)]" style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ticket.device_model}</span>
            <span className="text-[11px] bg-[var(--bg)] border border-[var(--border)] text-[var(--text3)] px-2 py-0.5 rounded font-bold uppercase tracking-wider" style={{ flexShrink: 0 }}>
              {ticket.device_brand}
            </span>
          </div>
          <div className="ticket-device-brand" style={{ fontFamily: "'Space Grotesk', monospace", color: "var(--accent)", display: "flex", alignItems: "center", gap: 8, marginTop: 4, fontSize: 12, flexWrap: "wrap" }}>
            <span>#{maskTrackingCode(ticket.tracking_token || String(ticket.id))}</span>
            <span style={{ color: "var(--text3)", fontSize: 10 }}>•</span>
            <span style={{ color: "var(--text2)", fontSize: 12, fontFamily: "inherit", fontWeight: 600 }}>
              {ticket.customer?.full_name || ticket._frontendName || ticket.client_email || "Cliente"}
            </span>
            <span style={{ color: "var(--text3)", fontSize: 10 }}>•</span>
            <span style={{ color: "var(--text3)", fontSize: 12, fontFamily: "inherit", display: "inline-flex", alignItems: "center", gap: 4 }}>
              <Clock size={12} /> {formatRelativeAge(ticket.created_at)}
            </span>
          </div>
        </div>
        <StatusBadge status={ticket.status} />
      </div>

      {/* SIGNALS / EXCEPTION BADGES */}
      <div className="ticket-card-signals" style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", margin: "10px 0 14px", padding: "0 20px" }}>
        <span style={{ color: ticket.technician ? "var(--text2)" : "var(--warning)", fontSize: 12, display: "inline-flex", alignItems: "center", gap: 4 }}>
          {ticket.technician ? <Wrench size={13} /> : <AlertTriangle size={13} />} {ticket.technician?.full_name || "Sin técnico"}
        </span>
        {renderExceptionBadges()}
      </div>

      {/* FOOTER: Smart Action + status select + save button + modal link */}
      <div className="ticket-card-footer" style={{ display: "flex", alignItems: "center", gap: 8, marginTop: "auto", flexWrap: "wrap" }}>
        {renderSmartAction()}
        <select
          className="status-select"
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          aria-label="Cambiar estado"
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
          style={{ marginLeft: "auto", fontSize: 12, color: "var(--info)", background: "none", border: "none", cursor: "pointer", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}
        >
          Ver detalle →
        </button>
      </div>

    </div>

    {/* REUSABLE DETAIL MODAL */}
    {showDetail && (
      <TicketDetailModal
        ticket={ticket}
        onClose={() => setShowDetail(false)}
        onStatusChange={onStatusChange}
      />
    )}

    {/* DIAGNOSTIC MODAL — smart action shortcut */}
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
