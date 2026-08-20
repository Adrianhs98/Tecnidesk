import { useState, useEffect, useCallback } from "react";
import { X, AlertTriangle, AlertCircle, Plus, Trash2, ClipboardList, Wrench } from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { formatCurrency } from "../../../utils/currency";

// Opciones predefinidas de reparaciones comunes
const QUICK_OPTIONS = [
  { id: "flex", label: "Pin de carga / Puerto USB" },
  { id: "display", label: "Cambio de pantalla / Display" },
  { id: "bateria", label: "Cambio de batería" },
  { id: "tapa", label: "Tapa trasera / Vidrio" },
  { id: "auricular", label: "Altavoz / Auricular / Micrófono" },
  { id: "custom", label: "✏️ Otro (escribir manualmente)" },
];

export default function DiagnosticModal({ ticketId, ticket, onClose, onSuccess }) {
  const [inventory, setInventory] = useState([]);
  const [loadingInv, setLoadingInv] = useState(false);

  // Paso 1: diagnóstico en texto
  const [diagNotes, setDiagNotes] = useState(ticket.diagnostic_notes || "");

  // Paso 2: selección de repuesto
  const [quickOption, setQuickOption] = useState(""); // id de QUICK_OPTIONS o id de inventario
  const [customName, setCustomName] = useState("");
  const [customPrice, setCustomPrice] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [pendingItems, setPendingItems] = useState([]); // items ya agregados en este flujo
  const [itemError, setItemError] = useState(null);
  const [addingItem, setAddingItem] = useState(false);

  // Submit final
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  // Cerrar con Escape
  const handleKeyDown = useCallback((e) => {
    if (e.key === "Escape") onClose();
  }, [onClose]);

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Cargar inventario activo
  useEffect(() => {
    let mounted = true;
    const fetchInv = async () => {
      setLoadingInv(true);
      try {
        const res = await authFetch(`${API_BASE}/inventory`);
        if (res.ok && mounted) {
          const data = await res.json();
          setInventory(Array.isArray(data) ? data : (data.items || []));
        }
      } catch (err) {
        console.error("Error loading inventory:", err);
      } finally {
        if (mounted) setLoadingInv(false);
      }
    };
    fetchInv();
    return () => { mounted = false; };
  }, []);

  const inventoryList = Array.isArray(inventory) ? inventory : (inventory?.items || []);

  // Determina si el formulario de repuesto muestra input de nombre/precio manual
  const isCustom = quickOption === "custom";
  const isInventoryItem = inventoryList.some(i => i.id === quickOption);
  const isQuickLabel = QUICK_OPTIONS.filter(o => o.id !== "custom").some(o => o.id === quickOption);

  // Obtener precio y nombre del item seleccionado
  const getSelectedItemData = () => {
    if (isInventoryItem) {
      const inv = inventoryList.find(i => i.id === quickOption);
      return { description: inv.item_name, unit_price: parseFloat(inv.selling_price), inventory_id: inv.id, item_type: "part" };
    }
    if (isQuickLabel) {
      const opt = QUICK_OPTIONS.find(o => o.id === quickOption);
      return { description: opt.label, unit_price: parseFloat(customPrice) || 0, inventory_id: null, item_type: "other" };
    }
    if (isCustom) {
      return { description: customName.trim(), unit_price: parseFloat(customPrice) || 0, inventory_id: null, item_type: "other" };
    }
    return null;
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    if (!quickOption) return;
    const data = getSelectedItemData();
    if (!data) return;

    if (!data.description || data.description.length < 2) {
      setItemError("Escribe el nombre del repuesto.");
      return;
    }
    if (data.unit_price <= 0) {
      setItemError("Ingresa un precio mayor a $0.");
      return;
    }

    setAddingItem(true);
    setItemError(null);

    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticketId}/items`, {
        method: "POST",
        body: JSON.stringify({
          inventory_id: data.inventory_id,
          item_type: data.item_type,
          description: data.description,
          quantity: parseInt(quantity),
          unit_price: data.unit_price,
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const newItem = await res.json();
      setPendingItems(prev => [...prev, newItem]);

      // Reset form
      setQuickOption("");
      setCustomName("");
      setCustomPrice("");
      setQuantity(1);
    } catch (err) {
      setItemError(err.message || "Error al agregar repuesto.");
    } finally {
      setAddingItem(false);
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticketId}/items/${itemId}`, { method: "DELETE" });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }
      setPendingItems(prev => prev.filter(i => i.id !== itemId));
    } catch (err) {
      setItemError(err.message || "Error al quitar repuesto.");
    }
  };

  const totalCost = pendingItems.reduce((acc, i) => acc + parseFloat(i.unit_price) * i.quantity, 0);
  const canSend = diagNotes.trim().length >= 5 && pendingItems.length > 0;

  const handleSend = async () => {
    if (!canSend) return;
    setSubmitting(true);
    setSubmitError(null);

    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticketId}/diagnostic`, {
        method: "PATCH",
        body: JSON.stringify({
          diagnostic_notes: diagNotes.trim(),
          labor_cost: 0, // sin mano de obra separada
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const updated = await res.json();
      onSuccess(updated);
    } catch (err) {
      setSubmitError(err.message || "Error al enviar diagnóstico.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 2000,
        background: "rgba(0,0,0,0.80)",
        display: "flex", alignItems: "center", justifyContent: "center",
        padding: 16,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
      role="dialog"
      aria-modal="true"
      aria-label="Enviar diagnóstico"
    >
      <div style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 14,
        width: "100%",
        maxWidth: 520,
        maxHeight: "90vh",
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
      }}>

        {/* Header */}
        <div style={{
          padding: "16px 20px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "var(--bg)",
          borderRadius: "14px 14px 0 0",
          position: "sticky",
          top: 0,
          zIndex: 1,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <ClipboardList size={18} color="var(--accent)" />
            <span style={{ fontSize: 16, fontWeight: 700, color: "var(--text1)" }}>
              Diagnóstico — {ticket.device_model}
            </span>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "var(--text3)", cursor: "pointer", display: "flex" }}
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Sección 1: Diagnóstico */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text3)", marginBottom: 8 }}>
              1. Descripción del diagnóstico
            </div>
            <textarea
              className="form-textarea"
              placeholder="Describe el problema encontrado y la solución aplicada..."
              value={diagNotes}
              onChange={(e) => setDiagNotes(e.target.value)}
              style={{ minHeight: 80, fontSize: 13, width: "100%", boxSizing: "border-box" }}
            />
            {diagNotes.trim().length > 0 && diagNotes.trim().length < 5 && (
              <div style={{ fontSize: 11, color: "var(--danger)", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
                <AlertTriangle size={11} /> Mínimo 5 caracteres.
              </div>
            )}
          </div>

          {/* Sección 2: Repuesto/Reparación */}
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text3)", marginBottom: 8 }}>
              2. Repuesto o reparación realizada
            </div>

            {itemError && (
              <div style={{ fontSize: 12, color: "var(--danger)", display: "flex", alignItems: "center", gap: 6, background: "rgba(157,92,82,0.08)", border: "1px solid rgba(157,92,82,0.2)", padding: "8px 12px", borderRadius: 8, marginBottom: 10 }}>
                <AlertCircle size={14} /> {itemError}
              </div>
            )}

            {/* Items ya agregados */}
            {pendingItems.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
                {pendingItems.map(item => (
                  <div key={item.id} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "8px 12px",
                    background: "rgba(201,167,106,0.05)",
                    border: "1px solid rgba(201,167,106,0.2)",
                    borderRadius: 8
                  }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text1)" }}>{item.description}</span>
                      <span style={{ fontSize: 11, color: "var(--text3)", fontFamily: "monospace" }}>
                        {item.quantity}x @ {formatCurrency(item.unit_price)}
                      </span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: "var(--accent)", fontFamily: "monospace" }}>
                        {formatCurrency(parseFloat(item.unit_price) * item.quantity)}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(item.id)}
                        style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", padding: 4, display: "flex" }}
                        title="Quitar"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}

                {/* Total */}
                <div style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "8px 12px",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text2)" }}>Total presupuesto:</span>
                  <span style={{ fontSize: 16, fontWeight: 700, color: "var(--success)", fontFamily: "monospace" }}>
                    {formatCurrency(totalCost)}
                  </span>
                </div>
              </div>
            )}

            {/* Formulario para agregar item */}
            <form onSubmit={handleAddItem} style={{
              display: "flex", flexDirection: "column", gap: 8,
              background: "var(--surface2)", padding: 14,
              borderRadius: 10, border: "1px solid var(--border)"
            }}>
              {/* Opciones rápidas predefinidas + inventario */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                {QUICK_OPTIONS.map(opt => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => { setQuickOption(opt.id); setCustomName(""); setCustomPrice(""); setItemError(null); }}
                    style={{
                      padding: "8px 10px",
                      fontSize: 12,
                      fontWeight: 500,
                      borderRadius: 8,
                      cursor: "pointer",
                      textAlign: "left",
                      background: quickOption === opt.id ? "rgba(201,167,106,0.15)" : "var(--bg)",
                      border: quickOption === opt.id ? "1.5px solid var(--accent)" : "1px solid var(--border)",
                      color: quickOption === opt.id ? "var(--accent)" : "var(--text2)",
                      transition: "background-color 0.15s, border-color 0.15s, color 0.15s",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              {/* Inventario como dropdown si hay items */}
              {inventoryList.length > 0 && (
                <select
                  className="status-select"
                  value={isInventoryItem ? quickOption : ""}
                  onChange={(e) => {
                    setQuickOption(e.target.value);
                    setCustomName("");
                    setCustomPrice("");
                    setItemError(null);
                  }}
                  style={{ fontSize: 12 }}
                >
                  <option value="">📦 Seleccionar desde inventario...</option>
                  {inventoryList.map(i => (
                    <option key={i.id} value={i.id} disabled={i.stock_quantity === 0}>
                      {i.stock_quantity <= i.low_stock_alert ? "⚠️ " : ""}{i.item_name} (Stock: {i.stock_quantity}) — {formatCurrency(i.selling_price)}
                    </option>
                  ))}
                </select>
              )}

              {loadingInv && <div style={{ fontSize: 11, color: "var(--text3)" }}>Cargando inventario...</div>}

              {/* Precio para opciones predefinidas y custom */}
              {(isQuickLabel || isCustom) && (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {isCustom && (
                    <input
                      className="form-input"
                      type="text"
                      placeholder="Nombre del repuesto/reparación..."
                      value={customName}
                      onChange={(e) => setCustomName(e.target.value)}
                      style={{ fontSize: 13 }}
                      required
                    />
                  )}
                  <div style={{ display: "flex", gap: 8 }}>
                    <input
                      className="form-input"
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Precio ($)"
                      value={customPrice}
                      onChange={(e) => setCustomPrice(e.target.value)}
                      style={{ flex: 1, fontSize: 13 }}
                      required
                    />
                    <input
                      className="form-input"
                      type="number"
                      min="1"
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      placeholder="Cant."
                      style={{ width: 70, fontSize: 13, textAlign: "center" }}
                      required
                    />
                  </div>
                </div>
              )}

              {/* Cantidad para item de inventario */}
              {isInventoryItem && (
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                  <span style={{ fontSize: 12, color: "var(--text2)", flex: 1 }}>
                    Cantidad:
                  </span>
                  <input
                    className="form-input"
                    type="number"
                    min="1"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    style={{ width: 80, fontSize: 13, textAlign: "center" }}
                    required
                  />
                </div>
              )}

              {quickOption && (
                <button
                  className="btn-primary"
                  type="submit"
                  disabled={addingItem}
                  style={{ padding: "9px 14px", fontSize: 13, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
                >
                  {addingItem ? "Agregando..." : (<><Plus size={14} /> Agregar al presupuesto</>)}
                </button>
              )}
            </form>
          </div>

          {/* Error submit */}
          {submitError && (
            <div style={{ fontSize: 12, color: "var(--danger)", display: "flex", alignItems: "center", gap: 6, background: "rgba(157,92,82,0.08)", border: "1px solid rgba(157,92,82,0.2)", padding: "10px 14px", borderRadius: 8 }}>
              <AlertTriangle size={14} /> {submitError}
            </div>
          )}

          {/* Indicador de requisitos */}
          {!canSend && (
            <div style={{ fontSize: 12, color: "var(--text3)", fontStyle: "italic", display: "flex", flexDirection: "column", gap: 4 }}>
              Para enviar al cliente necesitas:
              <span style={{ color: diagNotes.trim().length >= 5 ? "var(--success)" : "var(--danger)" }}>
                {diagNotes.trim().length >= 5 ? "✓" : "✗"} Diagnóstico (mín. 5 caracteres)
              </span>
              <span style={{ color: pendingItems.length > 0 ? "var(--success)" : "var(--danger)" }}>
                {pendingItems.length > 0 ? "✓" : "✗"} Al menos 1 repuesto o reparación
              </span>
            </div>
          )}

          {/* Botones finales */}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn-secondary"
              onClick={onClose}
              style={{ flex: 1, padding: "11px 16px", fontSize: 13 }}
            >
              Cancelar
            </button>
            <button
              className="btn-primary"
              onClick={handleSend}
              disabled={!canSend || submitting}
              style={{
                flex: 2,
                padding: "11px 16px",
                fontSize: 13,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
                opacity: canSend ? 1 : 0.45,
                cursor: canSend ? "pointer" : "not-allowed",
              }}
            >
              <Wrench size={14} />
              {submitting ? "Enviando..." : "Enviar diagnóstico al cliente ✓"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
