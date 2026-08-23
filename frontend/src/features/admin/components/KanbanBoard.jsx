import React, { useState, useMemo } from "react";
import KanbanColumn from "./KanbanColumn";
import TicketDetailModal from "./TicketDetailModal";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { NEXT_STATUS_MAP } from "./KanbanTicketCard";

export { NEXT_STATUS_MAP };

export const KANBAN_COLUMNS = [
  { id: "ingreso", title: "Ingreso / Recepción", statuses: ["EN_ESPERA_INGRESO", "RECIBIDO"], accentColor: "var(--accent)" },
  { id: "revision", title: "En Revisión & Diagnóstico", statuses: ["EN_REVISION"], accentColor: "#B89251" },
  { id: "espera", title: "Presupuesto & Espera", statuses: ["ESPERANDO_APROBACION", "ESPERANDO_REPUESTO"], accentColor: "#CC8F5A" },
  { id: "reparacion", title: "En Reparación", statuses: ["EN_REPARACION"], accentColor: "#6F9FCC" },
  { id: "listos", title: "Listo para Retirar", statuses: ["LISTO_PARA_RETIRAR"], accentColor: "var(--success)" },
];

export default function KanbanBoard({ tickets = [], onStatusChange, slaThresholds = null }) {
  const [selectedTicket, setSelectedTicket] = useState(null);

  const groupedTickets = useMemo(() => {
    const groups = {};
    KANBAN_COLUMNS.forEach((col) => {
      groups[col.id] = [];
    });

    tickets.forEach((ticket) => {
      const targetCol = KANBAN_COLUMNS.find((col) => col.statuses.includes(ticket.status));
      if (targetCol) {
        groups[targetCol.id].push(ticket);
      }
    });

    return groups;
  }, [tickets]);

  const handleQuickAdvance = async (ticket) => {
    const nextStatus = NEXT_STATUS_MAP[ticket.status];
    if (!nextStatus) return;

    // Phase 2 assignment guard interception:
    // If moving to EN_REPARACION and !ticket.technician, open detail modal to assign technician
    if (nextStatus === "EN_REPARACION" && !ticket.technician) {
      alert("Para pasar a 'En Reparación' es obligatorio tener un técnico asignado.");
      setSelectedTicket(ticket);
      return;
    }

    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
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
      alert(err.message || "Error al actualizar estado del equipo");
    }
  };

  return (
    <>
      <div className="kanban-board-container" data-testid="kanban-board">
        <div className="kanban-columns-track">
          {KANBAN_COLUMNS.map((column) => (
            <KanbanColumn
              key={column.id}
              column={column}
              tickets={groupedTickets[column.id] || []}
              onOpenDetail={(ticket) => setSelectedTicket(ticket)}
              onQuickAdvance={handleQuickAdvance}
              slaThresholds={slaThresholds}
            />
          ))}
        </div>
      </div>

      {selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onStatusChange={(updated) => {
            if (onStatusChange) onStatusChange(updated);
            setSelectedTicket(updated);
          }}
        />
      )}
    </>
  );
}
