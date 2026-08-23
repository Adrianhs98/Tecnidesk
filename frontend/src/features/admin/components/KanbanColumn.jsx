import React from "react";
import KanbanTicketCard from "./KanbanTicketCard";
import { Inbox } from "lucide-react";

export default function KanbanColumn({ column, tickets = [], onOpenDetail, onQuickAdvance, slaThresholds = null }) {
  return (
    <div className="kanban-column" data-column-id={column.id}>
      <div className="kanban-column-header" style={{ "--column-accent": column.accentColor }}>
        <div className="kanban-column-title">
          <span>{column.title}</span>
        </div>
        <span className="kanban-column-badge">{tickets.length}</span>
      </div>

      <div className="kanban-column-body">
        {tickets.length === 0 ? (
          <div className="kanban-column-empty">
            <Inbox size={20} style={{ opacity: 0.5 }} />
            <span>Sin equipos</span>
          </div>
        ) : (
          tickets.map((ticket) => (
            <KanbanTicketCard
              key={ticket.id}
              ticket={ticket}
              onOpenDetail={onOpenDetail}
              onQuickAdvance={onQuickAdvance}
              slaThresholds={slaThresholds}
            />
          ))
        )}
      </div>
    </div>
  );
}
