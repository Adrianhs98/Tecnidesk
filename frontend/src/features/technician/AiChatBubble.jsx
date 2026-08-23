import { Sparkles, Bot } from "lucide-react";

export default function AiChatBubble({ onClick, isOpen, activeTicketContext }) {
  return (
    <aside className="ai-chat-bubble-container" aria-label="Copiloto IA Flotante">
      <button
        type="button"
        className={`ai-fab-btn ${isOpen ? "is-open" : ""}`}
        onClick={onClick}
        aria-label={isOpen ? "Cerrar Copiloto IA" : "Abrir Copiloto IA"}
        data-testid="ai-chat-bubble-btn"
      >
        <div className="ai-fab-glow" />
        <div className="ai-fab-icon-wrap">
          <Bot size={22} className="ai-fab-bot-icon" />
          <Sparkles size={12} className="ai-fab-sparkle-icon" />
        </div>
        <span className="ai-fab-tooltip">
          {activeTicketContext
            ? `Copiloto (${activeTicketContext.device_model || "Equipo"})`
            : "Copiloto IA"}
        </span>
      </button>
    </aside>
  );
}
