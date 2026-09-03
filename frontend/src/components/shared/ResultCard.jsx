import { STATUS_CONFIG } from "../../utils/constants";
import { formatDate } from "../../utils/date";
import { formatCurrency } from "../../utils/currency";
import Stepper from "./Stepper";

export default function ResultCard({ data, onRefresh }) {
  const cfg = STATUS_CONFIG[data.status] || { label: data.status_label, color: "#C9A76A", icon: "INFO" };

  return (
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

      {data.requires_approval && (
        <div className="approval-wrap">
          <div className="approval-banner">
            <span style={{ fontSize: 22 }}>INFO</span>
            <div className="approval-text">
              <strong>Tu aprobacion es necesaria.</strong> El tecnico reviso tu equipo y esta esperando tu confirmacion para proceder. Comunicate con el taller.
            </div>
          </div>
        </div>
      )}

      <div className="info-grid" style={{ marginTop: data.requires_approval ? "16px" : "0" }}>
        <div className="info-tile full">
          <div className="tile-label">Problema reportado</div>
          <div className="tile-value">{data.issue_description}</div>
        </div>
        <div className="info-tile full">
          <div className="tile-label">Diagnostico tecnico</div>
          <div className={`tile-value ${!data.diagnostic_notes ? "empty" : ""}`}>
            {data.diagnostic_notes || "Pendiente de revision"}
          </div>
        </div>
        <div className="info-tile">
          <div className="tile-label">Presupuesto estimado</div>
          {data.total_cost ? <div className="tile-value cost">{formatCurrency(data.total_cost)}</div> : <div className="tile-value cost-pending">En evaluacion</div>}
        </div>
        <div className="info-tile">
          <div className="tile-label">Estado actual</div>
          <div className="tile-value" style={{ color: cfg.color, fontWeight: 600 }}>
            {data.status_label || cfg.label}
          </div>
        </div>
      </div>

      <div className="result-footer">
        <div>
          <div className="timestamp">
            Ingresado: <span>{formatDate(data.created_at)}</span>
          </div>
          <div className="timestamp" style={{ marginTop: 4 }}>
            Actualizado: <span>{formatDate(data.updated_at)}</span>
          </div>
        </div>
        <button className="refresh-btn" onClick={onRefresh}>
          Actualizar
        </button>
      </div>
    </div>
  );
}
