import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginPage from '../../pages/LoginPage';
import { ThemeProvider } from '../../context/ThemeContext';

const renderLoginPage = () => render(
  <ThemeProvider>
    <LoginPage />
  </ThemeProvider>
);

const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('LoginPage Component - Email Sanitization & Normalization', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        access_token: 'fake-jwt-token',
        role: 'admin',
        shop_name: 'Taller Central',
        user_full_name: 'Admin User',
      }),
    });
  });

  it('strips leading and trailing whitespace from email upon submission', async () => {
    renderLoginPage();

    const emailInput = screen.getByPlaceholderText('taller@correo.com');
    const passwordInput = screen.getByPlaceholderText('********');
    const submitBtn = screen.getByRole('button', { name: /Ingresar/i });

    fireEvent.change(emailInput, { target: { value: '   admin@taller.com   ' } });
    fireEvent.change(passwordInput, { target: { value: 'Secret123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const callArgs = global.fetch.mock.calls[0];
    const payload = JSON.parse(callArgs[1].body);

    expect(payload.email).toBe('admin@taller.com');
    expect(payload.password).toBe('Secret123!');
  });

  it('converts uppercase and mixed-case email to lowercase upon submission', async () => {
    renderLoginPage();

    const emailInput = screen.getByPlaceholderText('taller@correo.com');
    const passwordInput = screen.getByPlaceholderText('********');
    const submitBtn = screen.getByRole('button', { name: /Ingresar/i });

    fireEvent.change(emailInput, { target: { value: 'Admin@TALLER.Com' } });
    fireEvent.change(passwordInput, { target: { value: 'Secret123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const payload = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(payload.email).toBe('admin@taller.com');
  });

  it('strips whitespace and converts to lowercase simultaneously', async () => {
    renderLoginPage();

    fireEvent.change(screen.getByPlaceholderText('taller@correo.com'), { target: { value: '  Carlos.Tech@TALLER.COM  ' } });
    fireEvent.change(screen.getByPlaceholderText('********'), { target: { value: 'Secret123!' } });
    fireEvent.click(screen.getByRole('button', { name: /Ingresar/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    const payload = JSON.parse(global.fetch.mock.calls[0][1].body);
    expect(payload.email).toBe('carlos.tech@taller.com');
  });

  it('shows validation error and halts submission if username or password is blank', async () => {
    renderLoginPage();

    const emailInput = screen.getByPlaceholderText('taller@correo.com');
    const passwordInput = screen.getByPlaceholderText('********');
    const submitBtn = screen.getByRole('button', { name: /Ingresar/i });

    fireEvent.change(emailInput, { target: { value: '   ' } });
    fireEvent.change(passwordInput, { target: { value: 'Secret123!' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Por favor completa todos los campos/i)).toBeInTheDocument();
    });

    expect(global.fetch).not.toHaveBeenCalled();
  });
});
