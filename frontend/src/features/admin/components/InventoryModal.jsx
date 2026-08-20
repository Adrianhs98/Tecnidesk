import { useState, useEffect } from "react";
import { Plus, Trash2, Edit2, Package, Search, AlertTriangle, ArrowUpCircle, Check, X } from "lucide-react";
import { authFetch } from "../../../api/authFetch";
import { API_BASE } from "../../../api/config";
import { formatCurrency } from "../../../utils/currency";

const COMMON_SUGGESTIONS = [
  "Pin de carga USB tipo C",
  "Pin de carga micro USB",
  "Pin de carga Lightning iPhone",
  "Batería iPhone",
  "Batería Samsung",
  "Display ",
  "Flex de encendido",
  "Altavoz auricular",
  "Micrófono",
  "Tapa trasera"
];

export default function InventoryModal({ onClose }) {
  const [items, setItems] = useState([]);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Search & Pagination
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(0);
  const [limit, setLimit] = useState(10);
  
  // Form states
  const [showForm, setShowForm] = useState(false);
  const [editItem, setEditItem] = useState(null); // null when adding
  const [itemName, setItemName] = useState("");
  const [costPrice, setCostPrice] = useState("");
  const [sellingPrice, setSellingPrice] = useState("");
  const [stockQuantity, setStockQuantity] = useState("0");
  const [lowStockAlert, setLowStockAlert] = useState("3");
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState(null);

  // Restock states
  const [restockItemId, setRestockItemId] = useState(null);
  const [restockQty, setRestockQty] = useState("1");
  const [restockSaving, setRestockSaving] = useState(false);

  // Load inventory
  const fetchInventory = async () => {
    setLoading(true);
    setError(null);
    try {
      const skip = page * limit;
      let url = `${API_BASE}/inventory?skip=${skip}&limit=${limit}`;
      if (searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      const res = await authFetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      setItems(data.items || []);
      setTotalItems(data.total || 0);
    } catch (err) {
      setError(err.message || "Error al cargar el inventario.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [page, limit, searchQuery]);

  const handleOpenAdd = () => {
    setEditItem(null);
    setItemName("");
    setCostPrice("");
    setSellingPrice("");
    setStockQuantity("0");
    setLowStockAlert("3");
    setFormError(null);
    setShowForm(true);
  };

  const handleOpenEdit = (item) => {
    setEditItem(item);
    setItemName(item.item_name);
    setCostPrice(parseFloat(item.cost_price).toString());
    setSellingPrice(parseFloat(item.selling_price).toString());
    setLowStockAlert(item.low_stock_alert.toString());
    setFormError(null);
    setShowForm(true);
  };

  const handleSaveItem = async (e) => {
    e.preventDefault();
    const name = itemName.trim();
    if (!name) {
      setFormError("El nombre es requerido.");
      return;
    }
    if (name.toLowerCase() === "display") {
      setFormError("Debes especificar la marca y modelo para un Display (ej. 'Display Samsung A12').");
      return;
    }

    const cost = Number(costPrice);
    const selling = Number(sellingPrice);
    if (!Number.isFinite(cost) || cost < 0) {
      setFormError("El costo de compra debe ser un número válido no negativo.");
      return;
    }
    if (!Number.isFinite(selling) || selling < 0) {
      setFormError("El precio de venta debe ser un número válido no negativo.");
      return;
    }

    const alertVal = Number(lowStockAlert);
    if (!Number.isInteger(alertVal) || alertVal < 0) {
      setFormError("La alerta de stock bajo debe ser un número entero válido no negativo.");
      return;
    }

    const isEdit = !!editItem;
    let qty = 0;
    if (!isEdit) {
      qty = Number(stockQuantity);
      if (!Number.isInteger(qty) || qty < 0) {
        setFormError("El stock inicial debe ser un número entero válido no negativo.");
        return;
      }
    }

    setFormSaving(true);
    setFormError(null);

    const url = isEdit ? `${API_BASE}/inventory/${editItem.id}` : `${API_BASE}/inventory`;
    const method = isEdit ? "PATCH" : "POST";

    const payload = {
      item_name: name,
      cost_price: cost,
      selling_price: selling,
      low_stock_alert: alertVal,
      ...(!isEdit && { stock_quantity: qty })
    };

    try {
      const res = await authFetch(url, {
        method,
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const savedItem = await res.json();
      
      setShowForm(false);
      setEditItem(null);

      try {
        await fetchInventory(); // Refresh the list from the database to stay in sync
      } catch (err) {
        console.error("Guardado exitoso pero falló al actualizar la lista", err);
        if (isEdit) {
          setItems(prev => prev.map(item => item.id === savedItem.id ? savedItem : item));
        } else {
          setItems(prev => [savedItem, ...prev]);
        }
      }
    } catch (err) {
      setFormError(err.message || "Error al guardar el ítem.");
    } finally {
      setFormSaving(false);
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (!window.confirm("¿Seguro que deseas eliminar este repuesto? Si ya está asociado a tickets anteriores, se conservará en el historial pero se ocultará del inventario activo.")) return;

    try {
      const res = await authFetch(`${API_BASE}/inventory/${itemId}`, {
        method: "DELETE"
      });

      if (!res.ok) throw new Error(`Error ${res.status}`);
      
      setItems(prev => prev.filter(item => item.id !== itemId));
    } catch (err) {
      alert(err.message || "Error al eliminar el ítem.");
    }
  };

  const handleRestock = async (itemId) => {
    const qty = parseInt(restockQty);
    if (!qty || qty <= 0) return;

    setRestockSaving(true);
    try {
      const res = await authFetch(`${API_BASE}/inventory/${itemId}/restock`, {
        method: "POST",
        body: JSON.stringify({ quantity: qty })
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }

      const updated = await res.json();
      setItems(prev => prev.map(item => item.id === itemId ? updated : item));
      setRestockItemId(null);
      setRestockQty("1");
    } catch (err) {
      alert(err.message || "Error al reabastecer.");
    } finally {
      setRestockSaving(false);
    }
  };

  const filteredItems = items;

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-card" style={{ maxWidth: 640 }}>
        
        <div className="modal-header">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ background: "rgba(201, 167, 106, 0.1)", p: 8, borderRadius: 8, color: "var(--accent)", display: "flex", padding: 8 }}>
              <Package size={20} />
            </div>
            <div>
              <div className="modal-title">Gestión de Inventario</div>
              <div className="modal-subtitle">Controla el stock de repuestos y materiales de tu taller</div>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>X</button>
        </div>

        <div className="modal-body" style={{ maxHeight: "70vh", overflowY: "auto" }}>
          {error && (
            <div className="admin-error-bar" style={{ marginBottom: 12 }}>
              <span>ERROR</span> {error}
            </div>
          )}

          {/* Controls: Search + Add */}
          {!showForm && (
            <div style={{ display: "flex", gap: 10, marginBottom: 16, alignItems: "center" }}>
              <div style={{ position: "relative", flex: 1, display: "flex", alignItems: "center" }}>
                <Search size={16} style={{ position: "absolute", left: 12, color: "var(--text3)" }} />
                <input 
                  className="form-input" 
                  type="text" 
                  placeholder="Buscar repuesto..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ paddingLeft: 36, width: "100%", fontSize: 13 }}
                />
              </div>
              <select 
                className="form-input" 
                value={limit} 
                onChange={(e) => {
                  setLimit(Number(e.target.value));
                  setPage(0);
                }} 
                style={{ width: "auto", fontSize: 13 }}
              >
                <option value={10}>10 por página</option>
                <option value={20}>20 por página</option>
                <option value={50}>50 por página</option>
              </select>
              <button className="btn-new-ticket" onClick={handleOpenAdd} style={{ width: "auto", display: "flex", gap: 6 }}>
                <Plus size={16} /> Nuevo
              </button>
            </div>
          )}

          {/* Form container */}
          {showForm && (
            <form onSubmit={handleSaveItem} style={{ background: "var(--surface2)", padding: 16, borderRadius: 12, border: "1px solid var(--border)", marginBottom: 16, display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--accent)", borderBottom: "1px solid var(--border)", paddingBottom: 6, marginBottom: 4 }}>
                {editItem ? `Editar: ${editItem.item_name}` : "Agregar Nuevo Repuesto al Inventario"}
              </div>

              {formError && (
                <div style={{ fontSize: 12, color: "var(--danger)", display: "flex", alignItems: "center", gap: 6, background: "rgba(157, 92, 82, 0.08)", border: "1px solid rgba(157, 92, 82, 0.2)", padding: "8px 12px", borderRadius: 8 }}>
                  <AlertTriangle size={14} />
                  <span>{formError}</span>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Nombre del repuesto / material *</label>
                <input 
                  className="form-input" 
                  type="text" 
                  placeholder="ej. Batería iPhone 11 OEM" 
                  value={itemName} 
                  onChange={(e) => setItemName(e.target.value)} 
                  required
                />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6 }}>Sugerencias comunes:</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {COMMON_SUGGESTIONS.map((suggestion) => (
                      <button
                        key={suggestion}
                        type="button"
                        onClick={() => setItemName(suggestion)}
                        style={{
                          padding: "4px 8px",
                          fontSize: 11,
                          background: itemName === suggestion ? "rgba(201, 167, 106, 0.15)" : "var(--bg)",
                          border: itemName === suggestion ? "1px solid var(--accent)" : "1px solid var(--border)",
                          color: itemName === suggestion ? "var(--accent)" : "var(--text2)",
                          borderRadius: 6,
                          cursor: "pointer",
                          transition: "background-color 0.15s, border-color 0.15s, color 0.15s"
                        }}
                      >
                        {suggestion.trim()}
                      </button>
                    ))}
                  </div>
                  {(itemName.trim() === "Display" || itemName === "Display ") && (
                    <div style={{ fontSize: 11, color: "var(--accent)", marginTop: 6, display: "flex", alignItems: "center", gap: 4 }}>
                      💡 Completa la marca y modelo, ej. "Display Samsung A12"
                    </div>
                  )}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Costo de compra ($) *</label>
                  <input 
                    className="form-input" 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    placeholder="0.00" 
                    value={costPrice} 
                    onChange={(e) => setCostPrice(e.target.value)} 
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Precio de venta ($) *</label>
                  <input 
                    className="form-input" 
                    type="number" 
                    step="0.01" 
                    min="0" 
                    placeholder="0.00" 
                    value={sellingPrice} 
                    onChange={(e) => setSellingPrice(e.target.value)} 
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                {!editItem && (
                  <div className="form-group">
                    <label className="form-label">Stock inicial *</label>
                    <input 
                      className="form-input" 
                      type="number" 
                      min="0" 
                      placeholder="0" 
                      value={stockQuantity} 
                      onChange={(e) => setStockQuantity(e.target.value)} 
                      required
                    />
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Alerta stock bajo *</label>
                  <input 
                    className="form-input" 
                    type="number" 
                    min="0" 
                    placeholder="3" 
                    value={lowStockAlert} 
                    onChange={(e) => setLowStockAlert(e.target.value)} 
                    required
                  />
                  <p className="form-hint">Mínimo stock para encender alarma visual.</p>
                </div>
              </div>

              <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 8 }}>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)} disabled={formSaving}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary" style={{ width: "auto", padding: "10px 20px" }} disabled={formSaving}>
                  {formSaving ? "Guardando..." : "Guardar Repuesto"}
                </button>
              </div>
            </form>
          )}

          {/* List items */}
          {loading ? (
            <div style={{ display: "flex", justifyContent: "center", padding: "40px 0", color: "var(--text3)", fontSize: 13, gap: 10, alignItems: "center" }}>
              <span className="spinner" />
              Cargando repuestos...
            </div>
          ) : filteredItems.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {filteredItems.map(item => {
                const isLow = item.stock_quantity <= item.low_stock_alert;
                const isRestocking = restockItemId === item.id;

                return (
                  <div 
                    key={item.id} 
                    style={{ 
                      padding: "12px 16px", 
                      background: "var(--surface)", 
                      border: isLow ? "1px solid rgba(157, 92, 82, 0.3)" : "1px solid var(--border)", 
                      borderRadius: 12,
                      display: "flex",
                      flexDirection: "column",
                      gap: 8
                    }}
                  >
                    {/* Upper row: Title and Alert Badge */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text1)" }}>
                        {item.item_name}
                      </span>
                      {isLow ? (
                        <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 4, background: "rgba(157, 92, 82, 0.12)", color: "var(--danger)", border: "1px solid rgba(157, 92, 82, 0.2)" }}>
                          ⚠️ STOCK BAJO
                        </span>
                      ) : (
                        <span style={{ fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 4, background: "rgba(78, 159, 125, 0.12)", color: "var(--success)", border: "1px solid rgba(78, 159, 125, 0.2)" }}>
                          🟢 OK
                        </span>
                      )}
                    </div>

                    {/* Middle row: Stats */}
                    <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--text3)", fontFamily: "monospace", borderBottom: "1px solid var(--border)", paddingBottom: 8 }}>
                      <div>Stock: <strong style={{ color: isLow ? "var(--danger)" : "var(--text1)", fontSize: 13 }}>{item.stock_quantity}</strong></div>
                      <div>Costo: <strong style={{ color: "var(--text2)" }}>{formatCurrency(item.cost_price)}</strong></div>
                      <div>Venta: <strong style={{ color: "var(--accent)" }}>{formatCurrency(item.selling_price)}</strong></div>
                      <div>Alerta: <strong>≤{item.low_stock_alert}</strong></div>
                    </div>

                    {/* Lower row: Actions */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 4 }}>
                      {/* Restock Subform */}
                      {isRestocking ? (
                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                          <input 
                            className="form-input"
                            type="number" 
                            min="1" 
                            value={restockQty}
                            onChange={(e) => setRestockQty(e.target.value)}
                            style={{ width: 64, padding: "4px 8px", fontSize: 12, textAlign: "center" }}
                            autoFocus
                          />
                          <button 
                            className="btn-primary" 
                            onClick={() => handleRestock(item.id)}
                            disabled={restockSaving}
                            style={{ padding: 6, width: "auto", background: "var(--success)", display: "flex" }}
                            title="Confirmar"
                          >
                            <Check size={14} />
                          </button>
                          <button 
                            className="btn-secondary" 
                            onClick={() => { setRestockItemId(null); setRestockQty("1"); }}
                            style={{ padding: 6, width: "auto" }}
                            title="Cancelar"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <button 
                          className="btn-secondary" 
                          onClick={() => { setRestockItemId(item.id); setRestockQty("1"); }}
                          style={{ padding: "5px 10px", fontSize: 11, display: "flex", alignItems: "center", gap: 4, width: "auto" }}
                        >
                          <ArrowUpCircle size={12} />
                          <span>Reabastecer</span>
                        </button>
                      )}

                      {/* Edit & Delete */}
                      <div style={{ display: "flex", gap: 8 }}>
                        <button 
                          onClick={() => handleOpenEdit(item)}
                          style={{ background: "none", border: "none", color: "var(--info)", cursor: "pointer", display: "flex", padding: 6 }}
                          title="Editar repuesto"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button 
                          onClick={() => handleDeleteItem(item.id)}
                          style={{ background: "none", border: "none", color: "var(--danger)", cursor: "pointer", display: "flex", padding: 6 }}
                          title="Eliminar repuesto"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "40px 0", color: "var(--text3)", fontStyle: "italic", fontSize: 13 }}>
              {searchQuery ? "No se encontraron repuestos con ese nombre." : "No hay repuestos registrados en el inventario."}
            </div>
          )}
          
          {!loading && filteredItems.length > 0 && (
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 20 }}>
              <button 
                className="btn-secondary" 
                disabled={page === 0} 
                onClick={() => setPage(p => p - 1)}
                style={{ width: "auto" }}
              >
                Anterior
              </button>
              <span style={{ color: "var(--text)", alignSelf: "center", fontSize: 13 }}>
                Página {page + 1} de {Math.ceil(totalItems / limit) || 1} ({totalItems} totales)
              </span>
              <button 
                className="btn-secondary" 
                disabled={(page + 1) * limit >= totalItems} 
                onClick={() => setPage(p => p + 1)}
                style={{ width: "auto" }}
              >
                Siguiente
              </button>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cerrar</button>
        </div>

      </div>
    </div>
  );
}
