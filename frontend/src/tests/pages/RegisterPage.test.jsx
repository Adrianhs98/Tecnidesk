import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RegisterPage from '../../pages/RegisterPage';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('RegisterPage Component - WhatsApp Validation & Normalization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: 'user-123',
        shop_id: 'shop-123',
        shop_name: 'Taller Central',
        message: 'Taller creado con éxito',
        generated_password: 'temp-password-123',
      }),
    });
  });

  it('keeps submit button disabled when WhatsApp number is invalid', () => {
    render(<RegisterPage />);

    const shopInput = screen.getByPlaceholderText('ej. TecniCenter Guayaquil');
    const emailInput = screen.getByPlaceholderText('taller@correo.com');
    const phoneInput = screen.getByPlaceholderText('ej. 593991234567');
    const submitBtn = screen.getByRole('button', { name: /Crear cuenta/i });

    fireEvent.change(shopInput, { target: { value: 'Taller Central' } });
    fireEvent.change(emailInput, { target: { value: 'admin@taller.com' } });
    
    // Invalid: landline with 02
    fireEvent.change(phoneInput, { target: { value: '022345678' } });
    expect(submitBtn).toBeDisabled();

    // Invalid: letters
    fireEvent.change(phoneInput, { target: { value: '0991234abc' } });
    expect(submitBtn).toBeDisabled();

    // Invalid: too short
    fireEvent.change(phoneInput, { target: { value: '09912' } });
    expect(submitBtn).toBeDisabled();
  });

  it('enables submit button when valid Ecuadorian national mobile is entered', () => {
    render(<RegisterPage />);

    const shopInput = screen.getByPlaceholderText('ej. TecniCenter Guayaquil');
    const emailInput = screen.getByPlaceholderText('taller@correo.com');
    const phoneInput = screen.getByPlaceholderText('ej. 593991234567');
    const submitBtn = screen.getByRole('button', { name: /Crear cuenta/i });

    fireEvent.change(shopInput, { target: { value: 'Taller Central' } });
    fireEvent.change(emailInput, { target: { value: 'admin@taller.com' } });
    fireEvent.change(phoneInput, { target: { value: '0991234567' } });

    expect(submitBtn).not.toBeDisabled();
  });

  it('normalizes national Ecuadorian mobile (09...) to international (5939...) in submit payload', async () => {
    render(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText('ej. TecniCenter Guayaquil'), { target: { value: 'Taller Central' } });
    fireEvent.change(screen.getByPlaceholderText('taller@correo.com'), { target: { value: 'admin@taller.com' } });
    fireEvent.change(screen.getByPlaceholderText('ej. 593991234567'), { target: { value: '0991234567' } });

    fireEvent.click(screen.getByRole('button', { name: /Crear cuenta/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const callArgs = global.fetch.mock.calls[0];
    const payload = JSON.parse(callArgs[1].body);

    expect(payload.contact_whatsapp).toBe('593991234567');
    expect(payload.shop_name).toBe('Taller Central');
    expect(payload.email).toBe('admin@taller.com');
  });

  it('normalizes formatted international number (+593 99 123 4567) by stripping plus and spaces', async () => {
    render(<RegisterPage />);

    fireEvent.change(screen.getByPlaceholderText('ej. TecniCenter Guayaquil'), { target: { value: 'Taller Express' } });
    fireEvent.change(screen.getByPlaceholderText('taller@correo.com'), { target: { value: 'express@taller.com' } });
    fireEvent.change(screen.getByPlaceholderText('ej. 593991234567'), { target: { value: '+593 98 765 4321' } });

    fireEvent.click(screen.getByRole('button', { name: /Crear cuenta/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const payload = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(payload.contact_whatsapp).toBe('593987654321');
  });
});
