import { authFetch } from './authFetch';
import { API_BASE } from './config';

/**
 * Obtiene métricas operacionales de Lead Time, Cycle Time y Cuello de Botella.
 * @param {number} days - Ventana de análisis en días (default: 30)
 * @returns {Promise<Object>} CycleTimeAnalyticsResponse
 */
export const fetchCycleTimeAnalytics = async (days = 30) => {
  const response = await authFetch(`${API_BASE}/tickets/analytics/cycle-times?days=${days}`);
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al cargar métricas de ciclo");
  }
  return response.json();
};

export const getCycleTimeAnalytics = fetchCycleTimeAnalytics;
