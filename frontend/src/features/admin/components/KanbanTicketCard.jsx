import React from "react";
import { Clock, Wrench, AlertTriangle, ChevronRight } from "lucide-react";
import { formatRelativeAge, isTicketStale } from "../../../utils/date";
import { maskTrackingCode } from "../../../utils/privacy";

export const NEXT_STATUS_MAP = {
  EN_ESPERA_INGRESO: "EN_REVISION",
  RECIBIDO: "EN_REVISION",
  EN_REVISION: "ESPERANDO_APROBACION",
  ESPERANDO_APROBACION: "EN_REPARACION",
  ESPERANDO_REPUESTO: "EN_REPARACION",
  EN_REPARACION: "LISTO_PARA_RETIRAR",
};

export default function KanbanTicketCard({ ticket, onOpenDetail, onQuickAdvance, slaThresholds = null }) {
  const stale = isTicketStale(ticket.updated_at || ticket.created_at, ticket.status, slaThresholds);
  const nextStatus = NEXT_STATUS_MAP[ticket.status];
  const clientName = ticket.customer?.full_name || ticket._frontendName || ticket.client_email || "Cliente";
  const maskedToken = maskTrackingCode(ticket.tracking_token || String(ticket.id));

  return (
    <div
      className={`kanban-ticket-card kanban-card ${stale ? "kanban-card-danger is-stale" : ""}`}
      onClick={() => onOpenDetail && onOpenDetail(ticket)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpenDetail && onOpenDetail(ticket);
        }
      }}
      aria-label={`Ticket ${ticket.device_model} - ${clientName}`}
    >
      <div className="kanban-card-header">
        <span className="kanban-card-device">{ticket.device_model}</span>
        <span className="kanban-card-brand">{ticket.device_brand}</span>
      </div>

      <div className="kanban-card-meta">
        <div className="kanban-card-token-row">
          <span className="kanban-card-token">#{maskedToken}</span>
          <span>•</span>
          <span className="kanban-card-client">{clientName}</span>
        </div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 4, color: "var(--text3)", fontSize: 11 }}>
          <Clock size={11} /> {formatRelativeAge(ticket.created_at)}
        </div>
      </div>

      <div className="kanban-card-signals">
        {ticket.technician ? (
          <span className="kanban-tech-pill assigned" title="Técnico asignado">
            <Wrench size={11} /> {ticket.technician.full_name}
          </span>
        ) : (
          <span className="kanban-tech-pill unassigned" title="Sin técnico asignado">
            <AlertTriangle size={11} /> Sin técnico
          </span>
        )}

        {stale && (
          <span className="badge-exception badge-danger">
            <Clock size={11} /> Vencido
          </span>
        )}

        {ticket.status === "EN_REVISION" && !ticket.diagnostic_notes && (
          <span className="badge-exception badge-muted">
            <Wrench size={11} /> Sin diag.
          </span>
        )}
      </div>

      <div className="kanban-card-footer">
        {nextStatus && (
          <button
            type="button"
            className="kanban-btn-advance"
            onClick={(e) => {
              e.stopPropagation();
              onQuickAdvance && onQuickAdvance(ticket);
            }}
            title={`Avanzar a ${nextStatus}`}
            aria-label={`Avanzar ticket ${ticket.device_model}`}
          >
            <span>Avanzar</span>
            <ChevronRight size={12} />
          </button>
        )}
      </div>
    </div>
  );
}
