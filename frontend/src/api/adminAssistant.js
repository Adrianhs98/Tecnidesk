import { authFetch } from './authFetch';
import { API_BASE } from './config';

export const sendAdminAssistantQuery = async (message) => {
  const response = await authFetch(`${API_BASE}/admin/assistant/query`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error al consultar el asistente administrativo");
  }
  return response.json();
};
