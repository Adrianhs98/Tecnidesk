import { authFetch } from './authFetch';
import { API_BASE } from './config';

/**
 * Obtiene el perfil operativo del técnico autenticado.
 * @returns {Promise<Object>}
 */
export const getTechnicianMe = async () => {
  const response = await authFetch(`${API_BASE}/technicians/me`);
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al obtener perfil del técnico");
  }
  return response.json();
};

/**
 * Auto-asigna un ticket al técnico autenticado.
 * @param {string} ticketId
 * @returns {Promise<Object>}
 */
export const assignTicketToMe = async (ticketId) => {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}/assign-me`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al auto-asignar el ticket");
  }
  return response.json();
};

/**
 * Audita y revela el PIN/contraseña desencriptada del ticket.
 * @param {string} ticketId
 * @returns {Promise<{ device_password?: string, pin?: string }>}
 */
export const revealTicketPin = async (ticketId) => {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}/reveal-pin`, {
    method: 'POST',
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al revelar PIN del dispositivo");
  }
  return response.json();
};
