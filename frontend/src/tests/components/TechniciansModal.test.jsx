import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TechniciansModal from '../../features/admin/components/TechniciansModal';
import * as authFetchModule from '../../api/authFetch';

vi.mock('../../api/authFetch', () => ({
  authFetch: vi.fn(),
}));

describe('TechniciansModal Component - Client-Side Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default metrics response
    vi.mocked(authFetchModule.authFetch).mockImplementation(async (url) => {
      if (url.includes('/technicians/metrics')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            technicians: [],
            shop_totals: { total_tickets: 0, total_attributed: 0, total_delivered: 0 },
          }),
        };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({ id: 'tech-1', full_name: 'Carlos Mendez' }),
      };
    });
  });

  it('halts submission and shows inline error when full_name contains only whitespace', async () => {
    render(<TechniciansModal onClose={vi.fn()} />);

    // Wait for initial fetch to finish
    await waitFor(() => {
      expect(screen.getByText('+ Nuevo Técnico')).toBeInTheDocument();
    });

    // Switch to form view
    fireEvent.click(screen.getByText('+ Nuevo Técnico'));

    const nameInput = screen.getByPlaceholderText('Ej: Juan Pérez');
    fireEvent.change(nameInput, { target: { value: '   ' } });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /Guardar Técnico/i }));

    await waitFor(() => {
      expect(screen.getByText(/El nombre completo debe tener al menos 2 caracteres/i)).toBeInTheDocument();
    });

    // Verify authFetch was never called with POST /technicians
    const postCalls = vi.mocked(authFetchModule.authFetch).mock.calls.filter(
      ([url, opts]) => opts && opts.method === 'POST' && !url.includes('/metrics')
    );
    expect(postCalls.length).toBe(0);
  });

  it('normalizes payload by trimming full_name and converting whitespace optional fields to null', async () => {
    render(<TechniciansModal onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('+ Nuevo Técnico')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('+ Nuevo Técnico'));

    fireEvent.change(screen.getByPlaceholderText('Ej: Juan Pérez'), { target: { value: '   Carlos Mendez   ' } });
    fireEvent.change(screen.getByPlaceholderText('Teléfono o email'), { target: { value: '   ' } });
    fireEvent.change(screen.getByPlaceholderText('Ej: Microsoldadura, Apple, Pantallas'), { target: { value: '   ' } });

    fireEvent.click(screen.getByRole('button', { name: /Guardar Técnico/i }));

    await waitFor(() => {
      const postCalls = vi.mocked(authFetchModule.authFetch).mock.calls.filter(
        ([url, opts]) => opts && opts.method === 'POST' && !url.includes('/metrics')
      );
      expect(postCalls.length).toBe(1);
    });

    const postCall = vi.mocked(authFetchModule.authFetch).mock.calls.find(
      ([url, opts]) => opts && opts.method === 'POST' && !url.includes('/metrics')
    );
    const payload = JSON.parse(postCall[1].body);

    expect(payload.full_name).toBe('Carlos Mendez');
    expect(payload.contact).toBeNull();
    expect(payload.declared_specialty).toBeNull();
  });

  it('displays API error in inline error banner instead of alert', async () => {
    vi.mocked(authFetchModule.authFetch).mockImplementation(async (url, opts) => {
      if (opts && opts.method === 'POST') {
        return {
          ok: false,
          status: 400,
          json: async () => ({ detail: 'Ya existe un técnico con ese nombre' }),
        };
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          technicians: [],
          shop_totals: { total_tickets: 0, total_attributed: 0, total_delivered: 0 },
        }),
      };
    });

    render(<TechniciansModal onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('+ Nuevo Técnico')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('+ Nuevo Técnico'));

    fireEvent.change(screen.getByPlaceholderText('Ej: Juan Pérez'), { target: { value: 'Carlos Mendez' } });
    fireEvent.click(screen.getByRole('button', { name: /Guardar Técnico/i }));

    await waitFor(() => {
      expect(screen.getByText(/Ya existe un técnico con ese nombre/i)).toBeInTheDocument();
    });
  });
});
