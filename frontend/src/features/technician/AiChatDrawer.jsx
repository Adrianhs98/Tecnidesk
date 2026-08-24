import { useState, useRef, useEffect } from "react";
import {
  X,
  Send,
  Bot,
  Sparkles,
  Smartphone,
  Globe,
  Check,
  BookOpen,
  ArrowRight,
  RefreshCw,
  Cpu,
  Zap,
  HelpCircle,
  CornerDownLeft,
} from "lucide-react";
import {
  sendDiagnosticChat,
  sendFreeDiagnosticChat,
  confirmCorrection,
} from "../../api/diagnostic";

// Quick diagnostic prompt suggestions
const QUICK_PROMPTS = [
  { label: "⚡ Falla de carga", text: "El equipo no recibe carga ni muestra consumo en amperímetro. ¿Qué líneas y componentes debo medir?" },
  { label: "📱 Touch / Display", text: "¿Cuáles son las fallas más comunes de pantalla táctil y cómo diferenciar falla de display vs controlador en placa?" },
  { label: "🔋 Batería / Consumo", text: "El teléfono consume 0.45A apagado antes del botón de encendido. ¿Cómo identificar el corto en línea principal?" },
  { label: "🔊 Sin audio / Codec", text: "Falla de micrófono y altavoz en llamadas. ¿Procedimiento para diagnosticar IC de audio?" },
];

function MessageContent({ text }) {
  if (!text) return null;
  const lines = text.split("\n");

  return (
    <div className="ai-chat-markdown">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="ai-md-spacer" />;

        // Bullet lists
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          return (
            <div key={idx} className="ai-md-bullet">
              <span className="ai-md-bullet-dot">•</span>
              <span>{formatInline(trimmed.slice(2))}</span>
            </div>
          );
        }

        // Numbered steps
        const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
        if (numMatch) {
          return (
            <div key={idx} className="ai-md-numbered">
              <span className="ai-md-num-badge">{numMatch[1]}</span>
              <span>{formatInline(numMatch[2])}</span>
            </div>
          );
        }

        // Headers
        if (trimmed.startsWith("### ")) {
          return <h4 key={idx} className="ai-md-h4">{trimmed.slice(4)}</h4>;
        }
        if (trimmed.startsWith("## ")) {
          return <h3 key={idx} className="ai-md-h3">{trimmed.slice(3)}</h3>;
        }

        return <p key={idx} className="ai-md-p">{formatInline(trimmed)}</p>;
      })}
    </div>
  );
}

function formatInline(str) {
  const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i} className="ai-inline-code">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

export default function AiChatDrawer({
  isOpen,
  onClose,
  ticketContext = null,
  onClearTicketContext,
  onApplyToDiagnosis,
}) {
  const [messages, setMessages] = useState([
    {
      id: "welcome",
      role: "assistant",
      content:
        "👋 ¡Hola! Soy tu **Copiloto IA de Taller** (Gemini 3.7 Flash). Puedo ayudarte a diagnosticar cortos, analizar esquemas, interpretar consumos de fuente y resolver fallas complejas.",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // RAG learning modal/inline state
  const [showRagForm, setShowRagForm] = useState(false);
  const [ragForm, setRagForm] = useState({
    diagnosed_cause: "",
    solution_applied: "",
  });
  const [ragSuccess, setRagSuccess] = useState(false);
  const [ragSaving, setRagSaving] = useState(false);
  const [appliedSuccess, setAppliedSuccess] = useState(null);

  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  // When ticketContext changes, announce it in chat
  useEffect(() => {
    if (ticketContext) {
      setMessages((prev) => [
        ...prev,
        {
          id: `context-${ticketContext.id}-${Date.now()}`,
          role: "system",
          content: `🎯 **Contexto Activado:** Trabajando en **${ticketContext.device_brand} ${ticketContext.device_model}** (#${ticketContext.tracking_token || ticketContext.id?.slice(0, 8)}). Falla: "${ticketContext.issue_description || "Sin falla especificada"}"`,
        },
      ]);
    }
  }, [ticketContext]);

  const handleSendMessage = async (customText = null) => {
    const textToSend = typeof customText === "string" ? customText : inputMessage;
    if (!textToSend.trim() || isSending) return;

    const userText = textToSend.trim();
    setInputMessage("");
    setErrorMsg(null);

    const userMsgId = `user-${Date.now()}`;
    setMessages((prev) => [...prev, { id: userMsgId, role: "technician", content: userText }]);
    setIsSending(true);

    try {
      let response;
      if (ticketContext?.id) {
        response = await sendDiagnosticChat(ticketContext.id, userText);
      } else {
        response = await sendFreeDiagnosticChat(userText);
      }

      const assistantMsg = {
        id: response.id || `ai-${Date.now()}`,
        role: "assistant",
        content: response.content || response.text || "No se obtuvo respuesta del copiloto.",
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setErrorMsg(err.message || "Error al comunicarse con el Copiloto IA");
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Apply AI advice to active ticket diagnostic
  const handleApplyAdvice = (content) => {
    if (onApplyToDiagnosis && ticketContext) {
      onApplyToDiagnosis(content, ticketContext);
      setAppliedSuccess("¡Diagnóstico volcado a la orden activa!");
      setTimeout(() => setAppliedSuccess(null), 3000);
    }
  };

  // Open RAG Form with smart defaults
  const handleOpenRag = (lastAiContent) => {
    setRagForm({
      diagnosed_cause: ticketContext?.issue_description || "Causa identificada por técnico",
      solution_applied: lastAiContent ? lastAiContent.slice(0, 200) : "Procedimiento de reparación aplicado",
    });
    setShowRagForm(true);
    setRagSuccess(false);
  };

  // Confirm RAG Learning
  const handleConfirmRag = async (e) => {
    e.preventDefault();
    if (!ticketContext?.id) return;
    if (!ragForm.diagnosed_cause || !ragForm.solution_applied) return;

    setRagSaving(true);
    try {
      await confirmCorrection(ticketContext.id, {
        diagnosed_cause: ragForm.diagnosed_cause,
        solution_applied: ragForm.solution_applied,
      });
      setRagSuccess(true);
      setTimeout(() => {
        setShowRagForm(false);
        setRagSuccess(false);
      }, 2500);
    } catch (err) {
      alert("Error al confirmar aprendizaje RAG: " + err.message);
    } finally {
      setRagSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="ai-drawer-overlay" onClick={onClose} aria-hidden="true" />
      <aside
        className="ai-chat-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Copiloto IA de Taller"
        data-testid="ai-chat-drawer"
      >
        {/* Header */}
        <header className="ai-drawer-header">
          <div className="ai-drawer-brand">
            <div className="ai-avatar-badge">
              <Bot size={20} className="ai-avatar-icon" />
              <Sparkles size={12} className="ai-sparkle-dot" />
            </div>
            <div>
              <h3 className="ai-drawer-title">Copiloto IA Técnico</h3>
              <span className="ai-drawer-subtitle">Gemini 3.7 Flash • Diagnóstico & RAG</span>
            </div>
          </div>
          <button
            type="button"
            className="ai-drawer-close-btn"
            onClick={onClose}
            aria-label="Cerrar Copiloto IA"
          >
            <X size={18} />
          </button>
        </header>

        {/* Context Status Banner */}
        <div className="ai-context-banner">
          {ticketContext ? (
            <div className="ai-context-active" data-testid="ai-active-ticket-banner">
              <Smartphone size={15} />
              <div className="ai-context-text">
                <strong>{ticketContext.device_brand} {ticketContext.device_model}</strong>
                <span>#{ticketContext.tracking_token || ticketContext.id?.slice(0, 8)}</span>
              </div>
              {onClearTicketContext && (
                <button
                  type="button"
                  className="ai-context-detach-btn"
                  onClick={onClearTicketContext}
                  title="Cambiar a modo libre general"
                  aria-label="Desvincular ticket"
                >
                  <X size={13} />
                </button>
              )}
            </div>
          ) : (
            <div className="ai-context-free" data-testid="ai-free-mode-banner">
              <Globe size={14} />
              <span>Modo Asistente Libre (Consultas generales de microelectrónica)</span>
            </div>
          )}
        </div>

        {/* Feedback alerts */}
        {appliedSuccess && (
          <div className="ai-alert-banner success" role="status">
            <Check size={14} /> {appliedSuccess}
          </div>
        )}

        {/* Messages Stream */}
        <div className="ai-messages-stream" data-testid="ai-messages-stream">
          {messages.map((m) => {
            if (m.role === "system") {
              return (
                <div key={m.id} className="ai-msg-system">
                  <MessageContent text={m.content} />
                </div>
              );
            }

            const isAssistant = m.role === "assistant";
            return (
              <div
                key={m.id}
                className={`ai-msg-wrap ${isAssistant ? "assistant" : "technician"}`}
                data-testid={`ai-msg-${m.role}`}
              >
                <div className="ai-msg-bubble">
                  {isAssistant && (
                    <div className="ai-bubble-header">
                      <div className="ai-tag">
                        <Cpu size={12} /> Copiloto
                      </div>
                    </div>
                  )}
                  <MessageContent text={m.content} />

                  {/* Actions for Assistant replies when in Ticket Context */}
                  {isAssistant && ticketContext && m.id !== "welcome" && (
                    <div className="ai-bubble-actions">
                      <button
                        type="button"
                        className="ai-action-chip primary"
                        onClick={() => handleApplyAdvice(m.content)}
                        data-testid="apply-to-diagnosis-btn"
                      >
                        <Check size={12} />
                        <span>Aplicar al Diagnóstico</span>
                      </button>
                      <button
                        type="button"
                        className="ai-action-chip secondary"
                        onClick={() => handleOpenRag(m.content)}
                        data-testid="confirm-rag-btn"
                      >
                        <BookOpen size={12} />
                        <span>Confirmar Aprendizaje (RAG)</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isSending && (
            <div className="ai-msg-wrap assistant">
              <div className="ai-msg-bubble ai-thinking-bubble">
                <div className="ai-thinking-dots">
                  <span />
                  <span />
                  <span />
                </div>
                <span className="ai-thinking-label">Analizando esquemas y base de conocimiento...</span>
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="ai-alert-banner error" role="alert">
              {errorMsg}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* RAG Confirmation Inline Form / Dialog */}
        {showRagForm && ticketContext && (
          <div className="ai-rag-form-wrap" data-testid="ai-rag-form">
            <div className="ai-rag-form-header">
              <BookOpen size={16} />
              <h4>Confirmar Aprendizaje para Base de Conocimientos</h4>
              <button
                type="button"
                className="ai-rag-close"
                onClick={() => setShowRagForm(false)}
              >
                <X size={14} />
              </button>
            </div>
            {ragSuccess ? (
              <div className="ai-rag-success-msg">
                ✓ ¡Caso confirmado y almacenado en el índice vectorial del taller!
              </div>
            ) : (
              <form onSubmit={handleConfirmRag} className="ai-rag-form-body">
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: 11 }}>Causa Diagnosticada:</label>
                  <input
                    type="text"
                    className="form-input"
                    value={ragForm.diagnosed_cause}
                    onChange={(e) =>
                      setRagForm((p) => ({ ...p, diagnosed_cause: e.target.value }))
                    }
                    placeholder="Ej. Condensador C302 en corto en línea VDD_MAIN"
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: 11 }}>Solución Aplicada:</label>
                  <textarea
                    className="form-input"
                    rows={2}
                    value={ragForm.solution_applied}
                    onChange={(e) =>
                      setRagForm((p) => ({ ...p, solution_applied: e.target.value }))
                    }
                    placeholder="Ej. Reemplazo de condensador y limpieza ultrasónica"
                    required
                  />
                </div>
                <div className="ai-rag-form-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setShowRagForm(false)}
                    style={{ fontSize: 12, padding: "5px 10px" }}
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={ragSaving}
                    style={{ fontSize: 12, padding: "5px 12px" }}
                    data-testid="submit-rag-learning-btn"
                  >
                    {ragSaving ? "Guardando..." : "Confirmar Aprendizaje (RAG)"}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Quick Suggestion Chips */}
        <div className="ai-quick-chips">
          {QUICK_PROMPTS.map((qp, idx) => (
            <button
              key={idx}
              type="button"
              className="ai-chip-btn"
              onClick={() => handleSendMessage(qp.text)}
              disabled={isSending}
            >
              {qp.label}
            </button>
          ))}
        </div>

        {/* Input Bar */}
        <footer className="ai-drawer-footer">
          <div className="ai-input-wrapper">
            <textarea
              className="ai-chat-textarea"
              rows={2}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                ticketContext
                  ? `Pregunta sobre ${ticketContext.device_brand} ${ticketContext.device_model}...`
                  : "Pregunta al Copiloto técnico (Shift+Enter para salto de línea)..."
              }
              disabled={isSending}
              data-testid="ai-chat-input"
            />
            <button
              type="button"
              className="ai-send-btn"
              onClick={() => handleSendMessage()}
              disabled={!inputMessage.trim() || isSending}
              aria-label="Enviar mensaje al copiloto"
              data-testid="ai-send-btn"
            >
              <Send size={16} />
            </button>
          </div>
        </footer>
      </aside>
    </>
  );
}
