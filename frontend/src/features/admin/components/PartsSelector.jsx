import { useState, useEffect } from "react";
import { Plus, Trash2, AlertTriangle, AlertCircle } from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { formatCurrency } from "../../../utils/currency";

export default function PartsSelector({ ticketId, items, setItems, status, onItemsUpdated }) {
  const [inventory, setInventory] = useState([]);
  const [loadingInv, setLoadingInv] = useState(false);
  
  // Form state
  const [selectedInvId, setSelectedInvId] = useState("");
  const [customName, setCustomName] = useState("");
  const [customPrice, setCustomPrice] = useState("");
  const [quantity, setQuantity] = useState(1);
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const isReadOnly = ["ESPERANDO_APROBACION", "LISTO_PARA_RETIRAR", "NO_APROBADO"].includes(status);

  // Load active inventory items
  useEffect(() => {
    if (isReadOnly) return;
    let mounted = true;
    const fetchInventory = async () => {
      setLoadingInv(true);
      try {
        const res = await authFetch(`${API_BASE}/inventory`);
        if (res.ok && mounted) {
          setInventory(await res.json());
        }
      } catch (err) {
        console.error("Error fetching inventory:", err);
      } finally {
        if (mounted) setLoadingInv(false);
      }
    };
    fetchInventory();
    return () => { mounted = false; };
  }, [isReadOnly]);

  // Non-labor items (parts and other manual materials)
  const partsItems = items.filter(item => item.item_type !== "labor");

  // Calculate subtotal of parts
  const subtotalParts = partsItems.reduce((acc, item) => {
    return acc + (parseFloat(item.unit_price) * item.quantity);
  }, 0);

  const handleAddItem = async (e) => {
    e.preventDefault();
    if (!selectedInvId) return;

    setSubmitting(true);
    setError(null);

    let payload = {};

    if (selectedInvId === "custom") {
      if (!customName.trim() || customName.trim().length < 2) {
        setError("La descripción debe tener al menos 2 caracteres.");
        setSubmitting(false);
        return;
      }
      if (!customPrice || parseFloat(customPrice) < 0) {
        setError("Ingresa un precio válido.");
        setSubmitting(false);
        return;
      }
      payload = {
        inventory_id: null,
        item_type: "other",
        description: customName.trim(),
        quantity: parseInt(quantity),
        unit_price: parseFloat(customPrice)
      };
    } else {
      const invItem = inventory.find(i => i.id === selectedInvId);
      if (!invItem) {
        setError("Selección de inventario inválida.");
        setSubmitting(false);
        return;
      }
      payload = {
        inventory_id: invItem.id,
        item_type: "part",
        description: invItem.item_name,
        quantity: parseInt(quantity),
        unit_price: parseFloat(invItem.selling_price)
      };
    }

    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticketId}/items`, {
        method: "POST",
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const newItem = await res.json();
      setItems(prev => [...prev, newItem]);
      
      // Reset form
      setSelectedInvId("");
      setCustomName("");
      setCustomPrice("");
      setQuantity(1);

      if (onItemsUpdated) onItemsUpdated();
    } catch (err) {
      setError(err.message || "Error al agregar repuesto.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemoveItem = async (itemId) => {
    if (isReadOnly) return;
    if (!window.confirm("¿Seguro que deseas quitar este repuesto? Se restaurará el stock correspondiente.")) return;

    setError(null);
    try {
      const res = await authFetch(`${API_BASE}/tickets/${ticketId}/items/${itemId}`, {
        method: "DELETE"
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      setItems(prev => prev.filter(item => item.id !== itemId));
      
      if (onItemsUpdated) onItemsUpdated();
    } catch (err) {
      setError(err.message || "Error al quitar repuesto.");
    }
  };

  return (
    <div className="parts-selector-container" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text3)", marginTop: 8 }}>
        Repuestos y Materiales
      </div>

      {error && (
        <div style={{ fontSize: 12, color: "var(--danger)", display: "flex", alignItems: "center", gap: 6, background: "rgba(157, 92, 82, 0.08)", border: "1px solid rgba(157, 92, 82, 0.2)", padding: "8px 12px", borderRadius: 8 }}>
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* List of current parts */}
      {partsItems.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {partsItems.map(item => (
            <div 
              key={item.id} 
              style={{ 
                display: "flex", 
                justifyContent: "space-between", 
                alignItems: "center", 
                padding: "8px 12px", 
                background: "rgba(201, 167, 106, 0.04)", 
                border: "1px solid var(--border)", 
                borderRadius: 8 
              }}
            >
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: "var(--text1)" }}>
                  {item.description}
                </span>
                <span style={{ fontSize: 11, color: "var(--text3)", fontFamily: "monospace" }}>
                  {item.quantity}x @ {formatCurrency(item.unit_price)}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "var(--accent)", fontFamily: "monospace" }}>
                  {formatCurrency(parseFloat(item.unit_price) * item.quantity)}
                </span>
                {!isReadOnly && (
                  <button 
                    type="button"
                    onClick={() => handleRemoveItem(item.id)} 
                    style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", display: "flex", alignItems: "center", padding: 4 }}
                    title="Eliminar repuesto"
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: 12, color: "var(--text3)", fontStyle: "italic", padding: "8px 0" }}>
          Sin repuestos asociados a esta reparación.
        </div>
      )}

      {/* Subtotal piezas */}
      {partsItems.length > 0 && (
        <div style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px dashed var(--border)", fontSize: 13 }}>
          <span style={{ color: "var(--text2)" }}>Subtotal Repuestos:</span>
          <span style={{ fontWeight: 600, fontFamily: "monospace", color: "var(--text1)" }}>
            {formatCurrency(subtotalParts)}
          </span>
        </div>
      )}

      {/* Add Part Form */}
      {!isReadOnly && (
        <form onSubmit={handleAddItem} style={{ display: "flex", flexDirection: "column", gap: 8, background: "var(--surface2)", padding: 12, borderRadius: 10, border: "1px solid var(--border)" }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <select 
              className="status-select"
              value={selectedInvId} 
              onChange={(e) => {
                setSelectedInvId(e.target.value);
                setError(null);
              }}
              style={{ flex: 2, minWidth: 160, fontSize: 13 }}
            >
              <option value="">-- Seleccionar Repuesto --</option>
              
              {inventory.length > 0 && (
                <optgroup label="Repuestos en Inventario">
                  {inventory.map(i => {
                    const isLow = i.stock_quantity <= i.low_stock_alert;
                    return (
                      <option key={i.id} value={i.id} disabled={i.stock_quantity === 0}>
                        {isLow ? "⚠️ " : ""}{i.item_name} (Stock: {i.stock_quantity}) - {formatCurrency(i.selling_price)}
                      </option>
                    );
                  })}
                </optgroup>
              )}

              <option value="custom">Otro (escribir manualmente)...</option>
            </select>

            {selectedInvId && (
              <input 
                className="form-input"
                type="number" 
                min="1" 
                value={quantity} 
                onChange={(e) => setQuantity(e.target.value)} 
                placeholder="Cant."
                style={{ width: 70, textAlign: "center", fontSize: 13 }}
                required
              />
            )}
          </div>

          {selectedInvId === "custom" && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <input 
                className="form-input"
                type="text" 
                placeholder="Nombre del repuesto/material..." 
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                style={{ flex: 2, minWidth: 180, fontSize: 13 }}
                required
              />
              <input 
                className="form-input"
                type="number" 
                step="0.01" 
                min="0" 
                placeholder="Precio ($)" 
                value={customPrice}
                onChange={(e) => setCustomPrice(e.target.value)}
                style={{ width: 100, fontSize: 13 }}
                required
              />
            </div>
          )}

          {selectedInvId && (
            <button 
              className="btn-primary" 
              type="submit" 
              disabled={submitting}
              style={{ 
                padding: "8px 12px", 
                fontSize: 12, 
                display: "flex", 
                alignItems: "center", 
                justifyContent: "center", 
                gap: 6,
                marginTop: 4
              }}
            >
              {submitting ? "Agregando..." : (
                <>
                  <Plus size={14} />
                  <span>Agregar al Presupuesto</span>
                </>
              )}
            </button>
          )}
        </form>
      )}
    </div>
  );
}
