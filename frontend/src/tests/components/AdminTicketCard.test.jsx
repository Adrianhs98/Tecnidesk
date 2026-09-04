import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminTicketCard from '../../features/admin/components/AdminTicketCard';
import * as authFetchModule from '../../api/authFetch';

vi.mock('../../api/authFetch', () => ({
  authFetch: vi.fn(),
}));

describe('AdminTicketCard Component', () => {
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
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-08-21T16:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  const renderCard = (ticketProps = {}) => {
    const defaultTicket = {
      id: 'ticket-123',
      tracking_token: 'TRK-987654321',
      device_brand: 'Apple',
      device_model: 'iPhone 13 Pro',
      issue_description: 'Pantalla no enciende tras caída',
      diagnostic_notes: null,
      status: 'EN_REVISION',
      created_at: '2026-08-20T16:00:00.000Z', // 24h ago
      customer: {
        id: 'cust-1',
        full_name: 'Carlos Mendoza',
        phone_number: '0987654321',
        email: 'carlos@example.com',
      },
      technician: {
        id: 'tech-1',
        full_name: 'Juan Técnico',
      },
      device_password: 'SECRET_PIN_123',
      ...ticketProps,
    };

    return render(
      <QueryClientProvider client={queryClient}>
        <AdminTicketCard ticket={defaultTicket} onStatusChange={vi.fn()} />
      </QueryClientProvider>
    );
  };

  describe('Surface Declutter & Operational Signals', () => {
    it('renders device brand, model, masked token, client name, relative age, and status badge', () => {
      renderCard();

      expect(screen.getByText('iPhone 13 Pro')).toBeInTheDocument();
      expect(screen.getByText('Apple')).toBeInTheDocument();
      expect(screen.getByText(/#TRxxxxxx/)).toBeInTheDocument();
      expect(screen.getByText('Carlos Mendoza')).toBeInTheDocument();
      expect(screen.getByText('Ayer')).toBeInTheDocument();
      expect(screen.getAllByText('En revision').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('Juan Técnico')).toBeInTheDocument();
    });

    it('does NOT render PII, PIN, or issue description text on the card surface', () => {
      renderCard();

      // Issue description should NOT be on the surface
      expect(screen.queryByText('Pantalla no enciende tras caída')).not.toBeInTheDocument();
      // Raw/masked email should NOT be on the surface
      expect(screen.queryByText('carlos@example.com')).not.toBeInTheDocument();
      // PIN should NOT be on the surface
      expect(screen.queryByText('SECRET_PIN_123')).not.toBeInTheDocument();
    });

    it('does NOT fetch evidences on mount (prevents N+1 query issue)', () => {
      renderCard();
      const calls = vi.mocked(authFetchModule.authFetch).mock.calls;
      const evidenceCalls = calls.filter(([url]) => String(url).includes('/evidences'));
      expect(evidenceCalls.length).toBe(0);
    });
  });

  describe('Exception Badges', () => {
    it('displays "Sin técnico" badge exactly once when ticket has no technician', () => {
      renderCard({ technician: null });
      const badges = screen.getAllByText('Sin técnico');
      expect(badges.length).toBe(1);
    });

    it('displays "Sin diagnóstico" badge when status is EN_REVISION and diagnostic_notes is missing', () => {
      renderCard({ status: 'EN_REVISION', diagnostic_notes: null });
      expect(screen.getByText('Sin diagnóstico')).toBeInTheDocument();
    });

    it('displays "Vencido" badge with tooltip and marks card as is-stale when SLA is exceeded', () => {
      const fourDaysAgo = new Date('2026-08-17T12:00:00.000Z').toISOString();
      const { container } = renderCard({ created_at: fourDaysAgo, status: 'EN_REPARACION' });

      const staleBadge = screen.getByTestId('sla-stale-badge');
      expect(staleBadge).toBeInTheDocument();
      expect(staleBadge).toHaveTextContent('Vencido');
      expect(staleBadge).toHaveAttribute('title', 'Tiempo límite de atención superado (SLA vencido)');
      expect(container.querySelector('.ticket-card')).toHaveClass('is-stale');
    });

    it('displays "Listo p/ retiro" badge when status is LISTO_PARA_RETIRAR', () => {
      renderCard({ status: 'LISTO_PARA_RETIRAR' });
      expect(screen.getByText('Listo p/ retiro')).toBeInTheDocument();
    });

    it('displays "Esperando aprobación" badge when status is ESPERANDO_APROBACION', () => {
      renderCard({ status: 'ESPERANDO_APROBACION' });
      expect(screen.getByText('Esperando aprobación')).toBeInTheDocument();
    });

    it('displays no exception badges on a healthy assigned ticket with diagnosis', () => {
      const { container } = renderCard({
        status: 'EN_REPARACION',
        diagnostic_notes: 'Placa reparada',
        created_at: new Date('2026-08-21T10:00:00.000Z').toISOString(),
      });
      expect(screen.queryByText('Sin diagnóstico')).not.toBeInTheDocument();
      expect(screen.queryByText('Vencido')).not.toBeInTheDocument();
      expect(container.querySelector('.ticket-card')).not.toHaveClass('is-stale');
      expect(screen.queryByText('Listo p/ retiro')).not.toBeInTheDocument();
      expect(screen.queryByText('Esperando aprobación')).not.toBeInTheDocument();
    });
  });

  describe('Contextual Smart Action CTA', () => {
    it('priority 1: shows "Asignar" button when unassigned', () => {
      renderCard({ technician: null });
      const smartBtn = screen.getByRole('button', { name: /Asignar/i });
      expect(smartBtn).toBeInTheDocument();
    });

    it('priority 2: shows "Diagnosticar" button when EN_REVISION without diagnosis', () => {
      renderCard({
        technician: { id: 'tech-1', full_name: 'Tech 1' },
        status: 'EN_REVISION',
        diagnostic_notes: null,
      });
      const smartBtn = screen.getByRole('button', { name: /Diagnosticar/i });
      expect(smartBtn).toBeInTheDocument();
    });

    it('priority 3: shows "WhatsApp: Retiro" link when LISTO_PARA_RETIRAR', () => {
      renderCard({
        status: 'LISTO_PARA_RETIRAR',
        technician: { id: 'tech-1', full_name: 'Tech 1' },
      });
      const smartLink = screen.getByRole('link', { name: /WhatsApp: Retiro/i });
      expect(smartLink).toBeInTheDocument();
      expect(smartLink.getAttribute('href')).toContain('wa.me/593987654321');
    });

    it('priority 4: shows "WhatsApp: Seguimiento" link when ESPERANDO_APROBACION', () => {
      renderCard({
        status: 'ESPERANDO_APROBACION',
        technician: { id: 'tech-1', full_name: 'Tech 1' },
      });
      const smartLink = screen.getByRole('link', { name: /WhatsApp: Seguimiento/i });
      expect(smartLink).toBeInTheDocument();
      expect(decodeURIComponent(smartLink.getAttribute('href') || '')).toContain('tracking/TRK-987654321');
    });

    it('default: shows "Ver detalle" button when no special condition matches', () => {
      renderCard({
        status: 'EN_REPARACION',
        diagnostic_notes: 'Reparando',
        technician: { id: 'tech-1', full_name: 'Tech 1' },
      });
      const detailButtons = screen.getAllByRole('button', { name: /Ver detalle/i });
      expect(detailButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Detail Modal Deep Inspection', () => {
    it('opens modal on "Ver detalle" click and shows full details and fetches evidences', async () => {
      renderCard();
      const openDetailBtn = screen.getByRole('button', { name: /Ver detalles del equipo/i });
      fireEvent.click(openDetailBtn);

      // Verify modal is open
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Datos del Cliente')).toBeInTheDocument();
      expect(screen.getByText('Pantalla no enciende tras caída')).toBeInTheDocument();

      // Verify evidences were fetched now that modal is open
      const calls = vi.mocked(authFetchModule.authFetch).mock.calls;
      const evidenceCalls = calls.filter(([url]) => String(url).includes('/evidences'));
      expect(evidenceCalls.length).toBe(1);
    });

    it('toggles PII visibility in the modal', () => {
      renderCard();
      fireEvent.click(screen.getByRole('button', { name: /Ver detalles del equipo/i }));

      // Initially masked phone and email
      expect(screen.getByText(/09x+/)).toBeInTheDocument();
      expect(screen.getByText(/cax.*@example\.com/)).toBeInTheDocument();

      // Click "Ver" toggle
      const togglePiiBtn = screen.getByTitle('Mostrar datos');
      fireEvent.click(togglePiiBtn);

      // Now unmasked
      expect(screen.getByText('0987654321')).toBeInTheDocument();
      expect(screen.getByText('carlos@example.com')).toBeInTheDocument();
    });
  });
});
