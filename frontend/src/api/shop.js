import { authFetch } from './authFetch';
import { API_BASE } from './config';

/**
 * Obtiene la configuración de SLA del taller autenticado.
 * @returns {Promise<{ effective_thresholds: Object, custom_thresholds: Object, default_thresholds: Object }>}
 */
export const fetchSlaConfig = async () => {
  const response = await authFetch(`${API_BASE}/shops/sla-config`);
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al obtener configuración de SLAs");
  }
  return response.json();
};

export const getSlaConfig = fetchSlaConfig;

/**
 * Actualiza los umbrales personalizados de SLA para el taller.
 * @param {Object} customThresholds - Mapa de estado a horas de SLA (ej: { EN_REVISION: 12 })
 * @returns {Promise<{ effective_thresholds: Object, custom_thresholds: Object, default_thresholds: Object }>}
 */
export const updateSlaConfig = async (customThresholds) => {
  const response = await authFetch(`${API_BASE}/shops/sla-config`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ custom_thresholds: customThresholds }),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al actualizar configuración de SLAs");
  }
  return response.json();
};
