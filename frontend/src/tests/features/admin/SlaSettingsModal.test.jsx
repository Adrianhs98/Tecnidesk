import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SlaSettingsModal from '../../../features/admin/components/SlaSettingsModal';
import * as shopApi from '../../../api/shop';

vi.mock('../../../api/shop', () => ({
  fetchSlaConfig: vi.fn(),
  updateSlaConfig: vi.fn(),
}));

describe('SlaSettingsModal Component', () => {
  let queryClient;
  const mockOnClose = vi.fn();

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });

    vi.mocked(shopApi.fetchSlaConfig).mockResolvedValue({
      effective_thresholds: {
        EN_ESPERA_INGRESO: 48,
        EN_REVISION: 24,
        EN_REPARACION: 48,
      },
      custom_thresholds: {},
      default_thresholds: {
        EN_ESPERA_INGRESO: 48,
        EN_REVISION: 24,
        EN_REPARACION: 48,
      },
    });

    vi.mocked(shopApi.updateSlaConfig).mockResolvedValue({
      effective_thresholds: {
        EN_ESPERA_INGRESO: 48,
        EN_REVISION: 12,
        EN_REPARACION: 36,
      },
      custom_thresholds: {
        EN_REVISION: 12,
        EN_REPARACION: 36,
      },
      default_thresholds: {
        EN_ESPERA_INGRESO: 48,
        EN_REVISION: 24,
        EN_REPARACION: 48,
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderModal = (onClose = mockOnClose) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <SlaSettingsModal onClose={onClose} />
      </QueryClientProvider>
    );
  };

  it('renders modal with SLA status fields and current threshold values', async () => {
    renderModal();

    expect(screen.getByText('Configuración de Tiempos y Alertas')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText(/Horas SLA para En Espera de Ingreso/i)).toHaveValue(48);
      expect(screen.getByLabelText(/Horas SLA para En Revisión & Diagnóstico/i)).toHaveValue(24);
      expect(screen.getByLabelText(/Horas SLA para En Reparación/i)).toHaveValue(48);
    });

    expect(screen.getAllByText('Default: 48h')).toHaveLength(2);
    expect(screen.getByText('Default: 24h')).toBeInTheDocument();
  });

  it('validates minimum and maximum hour boundaries (1 to 720)', async () => {
    renderModal();

    const revisionInput = await screen.findByLabelText(/Horas SLA para En Revisión & Diagnóstico/i);

    // Test 0 hours (< 1)
    fireEvent.change(revisionInput, { target: { value: '0' } });
    await waitFor(() => {
      expect(screen.getByText(/Debe estar entre 1 y 720 horas/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Guardar Cambios/i })).toBeDisabled();
    });

    // Test 721 hours (> 720)
    fireEvent.change(revisionInput, { target: { value: '721' } });
    await waitFor(() => {
      expect(screen.getByText(/Debe estar entre 1 y 720 horas/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Guardar Cambios/i })).toBeDisabled();
    });

    // Test valid value
    fireEvent.change(revisionInput, { target: { value: '18' } });
    await waitFor(() => {
      expect(screen.queryByText(/Debe estar entre 1 y 720 horas/i)).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Guardar Cambios/i })).not.toBeDisabled();
    });
  });

  it('resets input fields to defaults when clicking "Restablecer Defaults"', async () => {
    renderModal();

    const revisionInput = await screen.findByLabelText(/Horas SLA para En Revisión & Diagnóstico/i);
    const reparacionInput = screen.getByLabelText(/Horas SLA para En Reparación/i);

    fireEvent.change(revisionInput, { target: { value: '6' } });
    fireEvent.change(reparacionInput, { target: { value: '72' } });

    expect(revisionInput).toHaveValue(6);
    expect(reparacionInput).toHaveValue(72);

    const resetBtn = screen.getByRole('button', { name: /Restablecer Defaults/i });
    fireEvent.click(resetBtn);

    expect(revisionInput).toHaveValue(24);
    expect(reparacionInput).toHaveValue(48);
  });

  it('submits updated SLA thresholds and displays success confirmation', async () => {
    renderModal();

    const revisionInput = await screen.findByLabelText(/Horas SLA para En Revisión & Diagnóstico/i);
    const reparacionInput = screen.getByLabelText(/Horas SLA para En Reparación/i);

    fireEvent.change(revisionInput, { target: { value: '12' } });
    fireEvent.change(reparacionInput, { target: { value: '36' } });

    const submitBtn = screen.getByRole('button', { name: /Guardar Cambios/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(shopApi.updateSlaConfig).toHaveBeenCalledWith({
        EN_ESPERA_INGRESO: 48,
        EN_REVISION: 12,
        EN_REPARACION: 36,
      });
      expect(screen.getByText(/Configuración de SLAs guardada correctamente/i)).toBeInTheDocument();
    });
  });

  it('calls onClose when clicking close button or pressing Escape key', async () => {
    renderModal();

    const closeBtn = await screen.findByRole('button', { name: /Cerrar modal/i });
    fireEvent.click(closeBtn);
    expect(mockOnClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(mockOnClose).toHaveBeenCalledTimes(2);
  });
});
