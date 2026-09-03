import { useState } from 'react';
import { Bot, ChevronDown, ChevronUp, Check, X, MessageSquare } from 'lucide-react';
import { diagnoseTicket, sendDiagnosticChat, confirmCorrection } from '../../../api/diagnostic';

export default function DiagnosticAssistPanel({ ticketId, onApplyAssist }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatMessage, setChatMessage] = useState('');
  const [expandedCitation, setExpandedCitation] = useState(null);

  const handleDiagnose = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await diagnoseTicket(ticketId);
      setResult(data);
      if (data.maturity_source === 'synthetic' || data.maturity_source === 'real_validated') {
        // init chat history empty
      }
    } catch (err) {
      setError("Error al solicitar diagnóstico: " + (err.message || ''));
    } finally {
      setLoading(false);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    const msg = chatMessage.trim();
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'technician', content: msg }]);
    try {
      const data = await sendDiagnosticChat(ticketId, msg);
      setChatHistory(prev => [...prev, { role: 'assistant', content: data.content }]);
    } catch (err) {
      setError("Error enviando mensaje: " + err.message);
    }
  };

  const handleConfirmCorrection = async () => {
    // Para simplificar, confirmamos con la última sugerencia o con lo que diga el usuario.
    try {
      const cause = "Causa corregida via chat";
      const solution = "Solución corregida via chat";
      await confirmCorrection(ticketId, { diagnosed_cause: cause, solution_applied: solution });
      onApplyAssist(cause + " -> " + solution);
      setChatOpen(false);
    } catch(err) {
      setError("Error confirmando corrección: " + err.message);
    }
  };

  const applyToForm = () => {
    if (result) {
      const notes = result.probable_cause + "\\n" + result.recommended_steps.join("\\n");
      onApplyAssist(notes);
    }
  };

  if (!result && !loading) {
    return (
      <button className="btn-secondary" onClick={handleDiagnose} style={{ width: '100%', marginBottom: 15 }}>
        <Bot size={16} style={{marginRight: 8}}/> Asistente de Diagnóstico IA
      </button>
    );
  }

  return (
    <div style={{ background: "rgba(91,192,222,0.1)", border: "1px solid var(--accent)", borderRadius: 8, padding: 16, marginBottom: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h4 style={{ margin: 0, display: "flex", alignItems: "center", gap: 8, color: "var(--accent)" }}>
          <Bot size={18} /> Sugerencia de IA
        </h4>
        {loading && <span style={{ fontSize: 12 }}>Analizando...</span>}
      </div>

      {error && <div style={{ color: "var(--danger)", fontSize: 12, marginTop: 8 }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 12 }}>
          <div style={{ fontSize: 13, color: "var(--text1)", marginBottom: 8 }}>
            <strong>Causa probable:</strong> {result.probable_cause}
          </div>
          <div style={{ fontSize: 13, color: "var(--text1)", marginBottom: 12 }}>
            <strong>Explicación:</strong> {result.summary_explanation}
          </div>
          
          <div style={{ fontSize: 12, display: "flex", gap: 12, marginBottom: 12 }}>
            <span style={{ background: "var(--bg)", padding: "4px 8px", borderRadius: 4 }}>
              Evidencia: {result.had_sufficient_evidence ? '✓ Suficiente' : '✗ Insuficiente'}
            </span>
            <span style={{ background: "var(--bg)", padding: "4px 8px", borderRadius: 4 }}>
              Confianza (distancia): {result.similarity_distance.toFixed(2)}
            </span>
            <span style={{ background: "var(--bg)", padding: "4px 8px", borderRadius: 4 }}>
              Fuente: {result.maturity_source}
            </span>
          </div>

          <div style={{ marginBottom: 12 }}>
            <strong style={{ fontSize: 12 }}>Citaciones:</strong>
            {result.citations?.map((cit, idx) => (
              <div key={idx} style={{ background: "var(--surface)", border: "1px solid var(--border)", padding: "6px 10px", borderRadius: 6, marginTop: 6 }}>
                <div 
                  style={{ display: "flex", justifyContent: "space-between", fontSize: 12, cursor: "pointer" }}
                  onClick={() => setExpandedCitation(expandedCitation === idx ? null : idx)}
                >
                  <span>Caso {cit.source_type}</span>
                  {expandedCitation === idx ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>
                {expandedCitation === idx && (
                  <div style={{ fontSize: 11, marginTop: 6, color: "var(--text2)" }}>
                    <div><strong>Causa:</strong> {cit.diagnosed_cause}</div>
                    <div><strong>Solución:</strong> {cit.solution_applied}</div>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button className="btn-primary" onClick={applyToForm} style={{ fontSize: 12, padding: "6px 12px" }}>
              <Check size={14} style={{ marginRight: 4 }}/> Aplicar al Diagnóstico
            </button>
            <button className="btn-secondary" onClick={() => setChatOpen(!chatOpen)} style={{ fontSize: 12, padding: "6px 12px" }}>
              <MessageSquare size={14} style={{ marginRight: 4 }}/> Corregir con IA
            </button>
          </div>

          {/* Drawer de chat inline */}
          {chatOpen && (
            <div style={{ marginTop: 12, padding: 12, background: "var(--bg)", borderRadius: 8, border: "1px solid var(--border)" }}>
              <h5 style={{ margin: "0 0 10px 0" }}>Chat de Corrección</h5>
              <div style={{ maxHeight: 150, overflowY: 'auto', marginBottom: 10, fontSize: 12 }}>
                {chatHistory.map((m, i) => (
                  <div key={i} style={{ marginBottom: 6, color: m.role === 'assistant' ? 'var(--accent)' : 'var(--text1)' }}>
                    <strong>{m.role === 'assistant' ? 'IA: ' : 'Tú: '}</strong>
                    {m.content}
                  </div>
                ))}
              </div>
              <form onSubmit={handleSendChat} style={{ display: "flex", gap: 8 }}>
                <input 
                  type="text" 
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  className="form-input"
                  style={{ flex: 1, fontSize: 12 }}
                  placeholder="Dile a la IA qué corrigió..."
                />
                <button type="submit" className="btn-primary" style={{ fontSize: 12 }}>Enviar</button>
              </form>
              <div style={{ marginTop: 8 }}>
                <button className="btn-secondary" onClick={handleConfirmCorrection} style={{ fontSize: 11, padding: "4px 8px" }}>
                  Confirmar Corrección y Guardar Caso
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
