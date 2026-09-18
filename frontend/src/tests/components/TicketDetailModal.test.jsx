import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import TicketDetailModal from '../../features/admin/components/TicketDetailModal';
import * as authFetchModule from '../../api/authFetch';
import { ADMIN_STATUSES } from '../../utils/constants';

vi.mock('../../api/authFetch', () => ({
  authFetch: vi.fn(),
}));

describe('TicketDetailModal Component', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });
    vi.mocked(authFetchModule.authFetch).mockResolvedValue({
      ok: true,
      json: async () => [],
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const mockTicket = {
    id: 'ticket-789',
    tracking_token: 'TRK-789456',
    device_brand: 'Samsung',
    device_model: 'Galaxy S22',
    issue_description: 'No enciende, posible corto en línea principal',
    status: 'EN_REVISION',
    diagnostic_notes: null,
    total_cost: 45.0,
    created_at: '2026-08-20T12:00:00.000Z',
    customer: {
      id: 'cust-2',
      full_name: 'Ana Belén',
      phone_number: '0991234567',
      email: 'ana@example.com',
    },
    technician: {
      id: 'tech-2',
      full_name: 'Marcos Rivas',
    },
    device_password: 'PIN-9999',
  };

  const renderModal = (props = {}) => {
    const defaultProps = {
      ticket: mockTicket,
      onClose: vi.fn(),
      onStatusChange: vi.fn(),
      ...props,
    };

    return {
      ...render(
        <QueryClientProvider client={queryClient}>
          <TicketDetailModal {...defaultProps} />
        </QueryClientProvider>
      ),
      props: defaultProps,
    };
  };

  describe('Administrative Status Management (7 States)', () => {
    it('renders the status control bar with all 7 administrative statuses in the dropdown', () => {
      renderModal();

      const statusSelect = screen.getByTestId('admin-ticket-status-select');
      expect(statusSelect).toBeInTheDocument();
      expect(statusSelect.value).toBe('EN_REVISION');

      const options = statusSelect.querySelectorAll('option');
      expect(options.length).toBe(7);

      const optionValues = Array.from(options).map((o) => o.value);
      expect(optionValues).toEqual(ADMIN_STATUSES.map((s) => s.value));
    });

    it('updates status directly from the modal and emits onStatusChange', async () => {
      const updatedTicket = { ...mockTicket, status: 'EN_REPARACION' };
      vi.mocked(authFetchModule.authFetch).mockImplementation(async (url, opts) => {
        if (String(url).includes('/status') && opts?.method === 'PATCH') {
          return {
            ok: true,
            json: async () => updatedTicket,
          };
        }
        return { ok: true, json: async () => [] };
      });

      const { props } = renderModal();
      const statusSelect = screen.getByTestId('admin-ticket-status-select');

      fireEvent.change(statusSelect, { target: { value: 'EN_REPARACION' } });

      await waitFor(() => {
        expect(authFetchModule.authFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tickets/ticket-789/status'),
          expect.objectContaining({
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'EN_REPARACION' }),
          })
        );
      });

      await waitFor(() => {
        expect(props.onStatusChange).toHaveBeenCalledWith(updatedTicket);
        expect(statusSelect.value).toBe('EN_REPARACION');
      });
    });

    it('renders error alert when status update fails', async () => {
      vi.mocked(authFetchModule.authFetch).mockImplementation(async (url, opts) => {
        if (String(url).includes('/status') && opts?.method === 'PATCH') {
          return {
            ok: false,
            status: 400,
            json: async () => ({ detail: 'Transición de estado no permitida' }),
          };
        }
        return { ok: true, json: async () => [] };
      });

      renderModal();
      const statusSelect = screen.getByTestId('admin-ticket-status-select');

      fireEvent.change(statusSelect, { target: { value: 'LISTO_PARA_RETIRAR' } });

      await waitFor(() => {
        expect(screen.getByText('Transición de estado no permitida')).toBeInTheDocument();
      });
    });
  });

  describe('Modal Accessibility and Interaction', () => {
    it('calls onClose when clicking close button or pressing Escape', () => {
      const { props } = renderModal();

      const closeBtn = screen.getByRole('button', { name: /Cerrar detalle/i });
      fireEvent.click(closeBtn);
      expect(props.onClose).toHaveBeenCalledTimes(1);

      fireEvent.keyDown(document, { key: 'Escape' });
      expect(props.onClose).toHaveBeenCalledTimes(2);
    });

    it('toggles PII visibility when clicking the toggle button', () => {
      renderModal();

      // Initially masked
      expect(screen.getByText(/09x+/)).toBeInTheDocument();
      expect(screen.getByText(/an.*@example\.com/)).toBeInTheDocument();

      const toggleBtn = screen.getByTitle('Mostrar datos');
      fireEvent.click(toggleBtn);

      // Unmasked
      expect(screen.getByText('0991234567')).toBeInTheDocument();
      expect(screen.getByText('ana@example.com')).toBeInTheDocument();
    });
  });
});
