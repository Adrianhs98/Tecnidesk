import { authFetch } from './authFetch';
import { API_BASE } from './config';

export const getMaturityMetric = async () => {
  const response = await authFetch(`${API_BASE}/diagnostic/maturity-metric`);
  if (!response.ok) throw new Error("Error fetching maturity metric");
  return response.json();
};

export const diagnoseTicket = async (ticketId) => {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}/diagnose`, { method: 'POST' });
  if (!response.ok) throw new Error("Error diagnosing ticket");
  return response.json();
};

export const sendDiagnosticChat = async (ticketId, message) => {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}/diagnostic-chat`, {
    method: 'POST',
    body: JSON.stringify({ message })
  });
  if (!response.ok) throw new Error("Error sending diagnostic chat");
  return response.json();
};

export const getDiagnosticChatHistory = async (ticketId) => {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}/diagnostic-chat`);
  if (!response.ok) throw new Error("Error loading diagnostic chat history");
  return response.json();
};

export const confirmCorrection = async (ticketId, data) => {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}/diagnostic-chat/confirm`, {
    method: 'POST',
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error("Error confirming correction");
  return response.json();
};

export const previewDiagnosis = async (brand, model, symptom) => {
  const response = await authFetch(`${API_BASE}/diagnostic/preview`, {
    method: 'POST',
    body: JSON.stringify({ brand, model, symptom })
  });
  if (!response.ok) throw new Error("Error previewing diagnosis");
  return response.json();
};

export const sendFreeDiagnosticChat = async (message) => {
  const response = await authFetch(`${API_BASE}/diagnostic/chat`, {
    method: 'POST',
    body: JSON.stringify({ message })
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || "Error sending free diagnostic chat");
  }
  return response.json();
};

