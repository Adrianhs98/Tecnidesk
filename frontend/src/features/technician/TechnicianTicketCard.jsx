import { useMemo } from "react";
import { Smartphone, Clock, AlertCircle, CheckCircle2, Wrench, ArrowRight, User } from "lucide-react";
import StatusBadge from "../../components/shared/StatusBadge";
import { formatRelativeAge, isTicketStale } from "../../utils/date";
import { maskPhone } from "../../utils/privacy";

export default function TechnicianTicketCard({
  ticket,
  onOpenWorkModal,
  onTakeTicket,
  isAvailable = false,
  isTaking = false,
  slaThresholds = null,
  isReadOnly = false,
}) {

  const isOverdue = useMemo(() => {
    return isTicketStale(ticket.updated_at || ticket.created_at, ticket.status, slaThresholds);
  }, [ticket.updated_at, ticket.created_at, ticket.status, slaThresholds]);

  const customerName = ticket.customer?.full_name || ticket.customer_name || "Cliente";
  const customerPhone = ticket.customer?.phone_number || ticket.customer_phone;
  const maskedPhone = customerPhone ? maskPhone(customerPhone) : null;

  return (
    <article
      className={`tech-ticket-card ${isOverdue ? "is-overdue" : ""}`}
      data-testid={`tech-ticket-card-${ticket.id}`}
    >
      <div className="tech-card-header">
        <div className="tech-card-device">
          <Smartphone size={16} className="tech-card-device-icon" />
          <span className="tech-card-brand">{ticket.device_brand}</span>
          <span className="tech-card-model">{ticket.device_model}</span>
        </div>
        <div className="tech-card-badges">
          <span
            className={`tech-sla-badge ${isOverdue ? "overdue" : "ontime"}`}
            title={isOverdue ? "Tiempo de SLA excedido" : "Dentro del tiempo de SLA"}
          >
            {isOverdue ? (
              <>
                <AlertCircle size={12} /> Vencido
              </>
            ) : (
              <>
                <CheckCircle2 size={12} /> A tiempo
              </>
            )}
          </span>
          <StatusBadge status={ticket.status} />
        </div>
      </div>

      <div className="tech-card-body">
        <div className="tech-card-tracking">
          <span className="mono">#{ticket.tracking_token || ticket.id?.slice(0, 8)}</span>
          <span className="tech-card-age">
            <Clock size={12} /> {formatRelativeAge(ticket.created_at)}
          </span>
        </div>

        <p className="tech-card-issue" title={ticket.issue_description}>
          <strong>Falla:</strong> {ticket.issue_description || "Sin descripción de falla"}
        </p>

        {customerPhone && (
          <div className="tech-card-customer">
            <User size={13} />
            <span>{customerName}</span>
            {maskedPhone && <span className="mono text-muted">({maskedPhone})</span>}
          </div>
        )}
      </div>

      <div className="tech-card-footer">
        {isReadOnly ? (
          <button
            type="button"
            className="btn-secondary tech-open-btn"
            onClick={() => onOpenWorkModal?.(ticket)}
            data-testid={`open-work-modal-${ticket.id}`}
          >
            <span>Ver Ficha (Lectura)</span>
            <ArrowRight size={14} />
          </button>
        ) : isAvailable ? (
          <button
            type="button"
            className="btn-primary tech-take-btn"
            onClick={() => onTakeTicket?.(ticket)}
            disabled={isTaking}
            data-testid={`take-ticket-btn-${ticket.id}`}
          >
            <Wrench size={14} />
            <span>{isTaking ? "Asignando..." : "Tomar Reparación"}</span>
          </button>
        ) : (
          <button
            type="button"
            className="btn-secondary tech-open-btn"
            onClick={() => onOpenWorkModal?.(ticket)}
            data-testid={`open-work-modal-${ticket.id}`}
          >
            <span>Trabajar en Equipo</span>
            <ArrowRight size={14} />
          </button>
        )}
      </div>
    </article>
  );
}
