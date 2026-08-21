import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { formatDate, formatOnlyDate, formatRelativeAge, isTicketStale } from '../../utils/date';

describe('Date Utilities', () => {
  describe('formatDate & formatOnlyDate', () => {
    it('returns "-" for null, undefined, or empty values', () => {
      expect(formatDate(null)).toBe('-');
      expect(formatDate(undefined)).toBe('-');
      expect(formatDate('')).toBe('-');
      expect(formatOnlyDate(null)).toBe('-');
      expect(formatOnlyDate(undefined)).toBe('-');
      expect(formatOnlyDate('')).toBe('-');
    });

    it('formats valid ISO strings', () => {
      const iso = '2026-08-20T14:30:00.000Z';
      expect(formatDate(iso)).toBeTruthy();
      expect(formatOnlyDate(iso)).toBeTruthy();
    });
  });

  describe('formatRelativeAge', () => {
    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-08-21T16:00:00.000Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns "-" for invalid or missing dates', () => {
      expect(formatRelativeAge(null)).toBe('-');
      expect(formatRelativeAge(undefined)).toBe('-');
      expect(formatRelativeAge('')).toBe('-');
      expect(formatRelativeAge('not-a-date')).toBe('-');
    });

    it('returns "Recién" when created less than 1 hour ago', () => {
      const halfHourAgo = new Date('2026-08-21T15:35:00.000Z').toISOString();
      expect(formatRelativeAge(halfHourAgo)).toBe('Recién');
    });

    it('returns "Hoy" when created earlier today (>= 1 hour ago)', () => {
      const earlierToday = new Date('2026-08-21T10:00:00.000Z').toISOString();
      expect(formatRelativeAge(earlierToday)).toBe('Hoy');
    });

    it('returns "Ayer" when created yesterday', () => {
      const yesterday = new Date('2026-08-20T14:00:00.000Z').toISOString();
      expect(formatRelativeAge(yesterday)).toBe('Ayer');
    });

    it('returns "Hace N días" for 2 to 6 days ago', () => {
      const threeDaysAgo = new Date('2026-08-18T16:00:00.000Z').toISOString();
      expect(formatRelativeAge(threeDaysAgo)).toBe('Hace 3 días');

      const fiveDaysAgo = new Date('2026-08-16T16:00:00.000Z').toISOString();
      expect(formatRelativeAge(fiveDaysAgo)).toBe('Hace 5 días');
    });

    it('returns "Hace N sems" or "Hace 1 sem" for 7 to 29 days ago', () => {
      const oneWeekAgo = new Date('2026-08-14T16:00:00.000Z').toISOString();
      expect(formatRelativeAge(oneWeekAgo)).toBe('Hace 1 sem');

      const twoWeeksAgo = new Date('2026-08-07T16:00:00.000Z').toISOString();
      expect(formatRelativeAge(twoWeeksAgo)).toBe('Hace 2 sems');
    });

    it('falls back to formatOnlyDate for 30+ days ago', () => {
      const fortyDaysAgo = new Date('2026-07-10T16:00:00.000Z').toISOString();
      expect(formatRelativeAge(fortyDaysAgo)).toBe(formatOnlyDate(fortyDaysAgo));
    });
  });

  describe('isTicketStale', () => {
    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date('2026-08-21T16:00:00.000Z'));
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns false for null, undefined, or empty values', () => {
      expect(isTicketStale(null, 'EN_REVISION')).toBe(false);
      expect(isTicketStale(undefined, 'EN_REVISION')).toBe(false);
      expect(isTicketStale('', 'EN_REVISION')).toBe(false);
    });

    it('returns false for closed or inactive statuses even if older than 72h', () => {
      const fourDaysAgo = new Date('2026-08-17T10:00:00.000Z').toISOString();
      expect(isTicketStale(fourDaysAgo, 'LISTO_PARA_RETIRAR')).toBe(false);
      expect(isTicketStale(fourDaysAgo, 'NO_APROBADO')).toBe(false);
      expect(isTicketStale(fourDaysAgo, 'ENTREGADO')).toBe(false);
    });

    it('returns false for active tickets created less than 72 hours ago', () => {
      const oneDayAgo = new Date('2026-08-20T16:00:00.000Z').toISOString();
      expect(isTicketStale(oneDayAgo, 'EN_REVISION')).toBe(false);

      const twoDaysAgo = new Date('2026-08-19T17:00:00.000Z').toISOString(); // 47 hours
      expect(isTicketStale(twoDaysAgo, 'EN_REPARACION')).toBe(false);
    });

    it('returns true for active tickets created 72 or more hours ago', () => {
      const exactly72HoursAgo = new Date('2026-08-18T16:00:00.000Z').toISOString();
      expect(isTicketStale(exactly72HoursAgo, 'EN_REVISION')).toBe(true);

      const fourDaysAgo = new Date('2026-08-17T12:00:00.000Z').toISOString();
      expect(isTicketStale(fourDaysAgo, 'EN_ESPERA_INGRESO')).toBe(true);
      expect(isTicketStale(fourDaysAgo, 'ESPERANDO_APROBACION')).toBe(true);
    });
  });
});
