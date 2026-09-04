import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import NewTicketModal from '../../features/admin/components/NewTicketModal';
import * as authFetchModule from '../../api/authFetch';

vi.mock('../../api/authFetch', () => ({
  authFetch: vi.fn(),
}));

describe('NewTicketModal Component - Phone Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(authFetchModule.authFetch).mockResolvedValue({
      ok: true,
      json: async () => ({ id: 'ticket-new-1', tracking_token: 'TRK-123' }),
      headers: new Headers(),
    });
  });

  it('renders phone format hint under the phone input', () => {
    render(<NewTicketModal onClose={vi.fn()} onCreated={vi.fn()} />);

    expect(screen.getByText(/Formato celular: 09XXXXXXXX o \+5939XXXXXXXX/i)).toBeInTheDocument();
  });

  it('blocks submit and shows error if an invalid Ecuadorian mobile phone is entered', async () => {
    render(<NewTicketModal onClose={vi.fn()} onCreated={vi.fn()} />);

    // Fill required fields
    fireEvent.change(screen.getByPlaceholderText('cliente@correo.com'), { target: { value: 'cliente@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('ej. Samsung'), { target: { value: 'Samsung' } });
    fireEvent.change(screen.getByPlaceholderText('ej. Galaxy S22'), { target: { value: 'Galaxy A12' } });
    fireEvent.change(screen.getByPlaceholderText(/Describe el problema/i), { target: { value: 'Pantalla partida' } });

    // Enter invalid phone (landline or short)
    fireEvent.change(screen.getByPlaceholderText('ej. 0991234567'), { target: { value: '022345678' } });

    // Click submit
    fireEvent.click(screen.getByRole('button', { name: /Guardar ticket/i }));

    await waitFor(() => {
      expect(screen.getByText(/Por favor ingresa un numero de celular valido/i)).toBeInTheDocument();
    });

    // authFetch should not have been called with POST /tickets
    const postCalls = vi.mocked(authFetchModule.authFetch).mock.calls.filter(
      ([url, opts]) => opts && opts.method === 'POST'
    );
    expect(postCalls.length).toBe(0);
  });

  it('sanitizes formatted phone number and submits successfully with clean phone', async () => {
    const onCreated = vi.fn();
    render(<NewTicketModal onClose={vi.fn()} onCreated={onCreated} />);

    // Fill required fields
    fireEvent.change(screen.getByPlaceholderText('cliente@correo.com'), { target: { value: 'cliente@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('ej. Samsung'), { target: { value: 'Samsung' } });
    fireEvent.change(screen.getByPlaceholderText('ej. Galaxy S22'), { target: { value: 'Galaxy A12' } });
    fireEvent.change(screen.getByPlaceholderText(/Describe el problema/i), { target: { value: 'Pantalla partida' } });

    // Enter formatted mobile phone
    fireEvent.change(screen.getByPlaceholderText('ej. 0991234567'), { target: { value: '099 123-4567' } });

    // Click submit
    fireEvent.click(screen.getByRole('button', { name: /Guardar ticket/i }));

    await waitFor(() => {
      expect(onCreated).toHaveBeenCalled();
    });

    const postCall = vi.mocked(authFetchModule.authFetch).mock.calls.find(
      ([url, opts]) => opts && opts.method === 'POST'
    );
    expect(postCall).toBeDefined();

    const payload = JSON.parse(postCall[1].body);
    expect(payload.client_phone).toBe('0991234567');
  });
});
