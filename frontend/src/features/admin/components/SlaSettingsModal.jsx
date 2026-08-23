import React, { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { X, Sliders, RotateCcw, AlertTriangle, Check, Clock } from "lucide-react";
import { fetchSlaConfig, updateSlaConfig } from "../../../api/shop";

const SLA_STATUS_FIELDS = [
  {
    key: "EN_ESPERA_INGRESO",
    label: "En Espera de Ingreso",
    description: "Tiempo máximo antes de que el equipo sea recibido o inspeccionado inicialmente.",
    defaultHours: 48,
  },
  {
    key: "EN_REVISION",
    label: "En Revisión & Diagnóstico",
    description: "Tiempo máximo para realizar el diagnóstico y emitir el presupuesto.",
    defaultHours: 24,
  },
  {
    key: "EN_REPARACION",
    label: "En Reparación",
    description: "Tiempo máximo de trabajo técnico en el banco una vez aprobado el presupuesto.",
    defaultHours: 48,
  },
];

export default function SlaSettingsModal({ onClose }) {
  const queryClient = useQueryClient();

  const { data: configData, isLoading, isError, error } = useQuery({
    queryKey: ["shopSlaConfig"],
    queryFn: fetchSlaConfig,
  });

  const [thresholds, setThresholds] = useState({
    EN_ESPERA_INGRESO: 48,
    EN_REVISION: 24,
    EN_REPARACION: 48,
  });
  const [validationErrors, setValidationErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState(null);

  useEffect(() => {
    if (configData?.effective_thresholds) {
      setThresholds({
        EN_ESPERA_INGRESO: configData.effective_thresholds.EN_ESPERA_INGRESO ?? 48,
        EN_REVISION: configData.effective_thresholds.EN_REVISION ?? 24,
        EN_REPARACION: configData.effective_thresholds.EN_REPARACION ?? 48,
      });
    }
  }, [configData]);

  // Modal keyboard accessibility
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = "unset";
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  const validateField = (key, value) => {
    const num = Number(value);
    if (!value || isNaN(num) || !Number.isInteger(num)) {
      return "Debe ser un número entero.";
    }
    if (num < 1 || num > 720) {
      return "Debe estar entre 1 y 720 horas (máx. 30 días).";
    }
    return null;
  };

  const handleInputChange = (key, value) => {
    setThresholds((prev) => ({ ...prev, [key]: value }));
    const err = validateField(key, value);
    setValidationErrors((prev) => ({ ...prev, [key]: err }));
    setSuccessMessage(null);
  };

  const mutation = useMutation({
    mutationFn: (newThresholds) => updateSlaConfig(newThresholds),
    onSuccess: (updatedData) => {
      queryClient.setQueryData(["shopSlaConfig"], updatedData);
      queryClient.invalidateQueries({ queryKey: ["dashboardData"] });
      setSuccessMessage("Configuración de SLAs guardada correctamente.");
      setTimeout(() => {
        onClose();
      }, 900);
    },
  });

  const hasErrors = Object.values(validationErrors).some(Boolean);

  const handleSubmit = (e) => {
    e.preventDefault();
    const currentErrors = {};
    const parsedPayload = {};

    SLA_STATUS_FIELDS.forEach(({ key }) => {
      const err = validateField(key, thresholds[key]);
      if (err) currentErrors[key] = err;
      parsedPayload[key] = parseInt(thresholds[key], 10);
    });

    if (Object.keys(currentErrors).length > 0) {
      setValidationErrors(currentErrors);
      return;
    }

    mutation.mutate(parsedPayload);
  };

  const handleResetDefaults = () => {
    const defaults = {
      EN_ESPERA_INGRESO: 48,
      EN_REVISION: 24,
      EN_REPARACION: 48,
    };
    setThresholds(defaults);
    setValidationErrors({});
    setSuccessMessage(null);
  };

  return (
    <div
      className="modal-overlay"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.8)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 1000,
        padding: "16px",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Configuración de SLAs de Taller"
    >
      <div
        className="modal-content"
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "20px",
          width: "100%",
          maxWidth: "540px",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 20px 40px rgba(0,0,0,0.4)",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: "var(--bg)",
            borderRadius: "20px 20px 0 0",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "rgba(201,167,106,0.12)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--accent)",
              }}
            >
              <Sliders size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: "17px", fontWeight: "700", color: "var(--text1)", margin: 0 }}>
                Configuración de SLAs
              </h2>
              <p style={{ fontSize: "12px", color: "var(--text3)", margin: "2px 0 0" }}>
                Tiempos máximos de atención por estado operativo
              </p>
            </div>
          </div>
          <button
            className="btn-secondary"
            onClick={onClose}
            aria-label="Cerrar modal"
            style={{
              padding: "8px",
              borderRadius: "50%",
              border: "none",
              background: "transparent",
              cursor: "pointer",
              color: "var(--text3)",
              display: "flex",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: "24px", overflowY: "auto" }}>
          {isLoading ? (
            <div style={{ textAlign: "center", padding: "30px 0", color: "var(--text3)" }}>
              <div className="spinner" style={{ margin: "0 auto 10px" }} />
              Cargando configuración...
            </div>
          ) : isError ? (
            <div className="error-card" style={{ marginBottom: 16 }}>
              {error?.message || "Error al cargar configuración de SLAs."}
            </div>
          ) : (
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div style={{ fontSize: "13px", color: "var(--text2)", lineHeight: "1.5" }}>
                Los equipos que excedan estas horas serán marcados con la señal{" "}
                <span className="badge-exception badge-danger" style={{ display: "inline-flex", verticalAlign: "middle" }}>
                  <Clock size={11} /> Vencido
                </span>{" "}
                y tendrán prioridad de atención en el tablero y workbench.
              </div>

              {SLA_STATUS_FIELDS.map(({ key, label, description, defaultHours }) => {
                const currentVal = thresholds[key] ?? "";
                const err = validationErrors[key];

                return (
                  <div
                    key={key}
                    style={{
                      background: "var(--surface2)",
                      border: "1px solid var(--border)",
                      borderRadius: "12px",
                      padding: "16px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <label htmlFor={`sla-${key}`} style={{ fontSize: "14px", fontWeight: "600", color: "var(--text1)" }}>
                        {label}
                      </label>
                      <span style={{ fontSize: "11px", color: "var(--text3)" }}>
                        Default: {defaultHours}h
                      </span>
                    </div>
                    <p style={{ fontSize: "12px", color: "var(--text3)", marginBottom: "12px", lineHeight: "1.4" }}>
                      {description}
                    </p>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <input
                        id={`sla-${key}`}
                        type="number"
                        min="1"
                        max="720"
                        step="1"
                        required
                        className="form-input"
                        style={{ width: "120px", fontWeight: "600", fontSize: "14px" }}
                        value={currentVal}
                        onChange={(e) => handleInputChange(key, e.target.value)}
                        aria-label={`Horas SLA para ${label}`}
                      />
                      <span style={{ fontSize: "13px", color: "var(--text2)" }}>horas</span>
                      <span style={{ fontSize: "12px", color: "var(--text3)", marginLeft: "auto" }}>
                        ({(Number(currentVal) / 24).toFixed(1)} días)
                      </span>
                    </div>
                    {err && (
                      <div
                        style={{
                          fontSize: "11px",
                          color: "var(--danger)",
                          marginTop: "6px",
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <AlertTriangle size={12} /> {err}
                      </div>
                    )}
                  </div>
                );
              })}

              {mutation.isError && (
                <div
                  style={{
                    padding: "10px 14px",
                    borderRadius: "8px",
                    background: "rgba(239, 68, 68, 0.1)",
                    border: "1px solid var(--danger)",
                    color: "var(--danger)",
                    fontSize: "12px",
                  }}
                >
                  {mutation.error?.message || "Error al actualizar SLAs."}
                </div>
              )}

              {successMessage && (
                <div
                  style={{
                    padding: "10px 14px",
                    borderRadius: "8px",
                    background: "rgba(34, 197, 94, 0.1)",
                    border: "1px solid var(--success)",
                    color: "var(--success)",
                    fontSize: "12px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Check size={14} /> {successMessage}
                </div>
              )}

              <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={handleResetDefaults}
                  disabled={mutation.isPending}
                  style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}
                  title="Restablecer a 48h / 24h / 48h"
                >
                  <RotateCcw size={14} /> Restablecer Defaults
                </button>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={onClose}
                  disabled={mutation.isPending}
                  style={{ marginLeft: "auto", fontSize: "13px" }}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={hasErrors || mutation.isPending}
                  style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px" }}
                >
                  {mutation.isPending ? (
                    <>
                      <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                      Guardando...
                    </>
                  ) : (
                    "Guardar Cambios"
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
