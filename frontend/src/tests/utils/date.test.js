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

    it('returns false for closed, terminal or paused statuses even if older than 72h', () => {
      const fourDaysAgo = new Date('2026-08-17T10:00:00.000Z').toISOString();
      expect(isTicketStale(fourDaysAgo, 'LISTO_PARA_RETIRAR')).toBe(false);
      expect(isTicketStale(fourDaysAgo, 'NO_APROBADO')).toBe(false);
      expect(isTicketStale(fourDaysAgo, 'ENTREGADO')).toBe(false);
      expect(isTicketStale(fourDaysAgo, 'ESPERANDO_APROBACION')).toBe(false);
      expect(isTicketStale(fourDaysAgo, 'ESPERANDO_REPUESTO')).toBe(false);
    });

    it('evaluates dynamic status SLAs correctly (24h for EN_REVISION, 48h for EN_ESPERA_INGRESO and EN_REPARACION)', () => {
      // 20 hours ago -> false for all (including EN_REVISION)
      const twentyHoursAgo = new Date('2026-08-20T20:00:00.000Z').toISOString();
      expect(isTicketStale(twentyHoursAgo, 'EN_REVISION')).toBe(false);
      expect(isTicketStale(twentyHoursAgo, 'EN_ESPERA_INGRESO')).toBe(false);
      expect(isTicketStale(twentyHoursAgo, 'EN_REPARACION')).toBe(false);

      // 25 hours ago -> true for EN_REVISION (>=24h), false for EN_ESPERA_INGRESO / EN_REPARACION (<48h)
      const twentyFiveHoursAgo = new Date('2026-08-20T15:00:00.000Z').toISOString();
      expect(isTicketStale(twentyFiveHoursAgo, 'EN_REVISION')).toBe(true);
      expect(isTicketStale(twentyFiveHoursAgo, 'EN_ESPERA_INGRESO')).toBe(false);
      expect(isTicketStale(twentyFiveHoursAgo, 'EN_REPARACION')).toBe(false);

      // 50 hours ago -> true for EN_ESPERA_INGRESO and EN_REPARACION (>=48h)
      const fiftyHoursAgo = new Date('2026-08-19T14:00:00.000Z').toISOString();
      expect(isTicketStale(fiftyHoursAgo, 'EN_ESPERA_INGRESO')).toBe(true);
      expect(isTicketStale(fiftyHoursAgo, 'EN_REPARACION')).toBe(true);
    });

    it('respects custom workshop threshold overrides when provided', () => {
      const customThresholds = {
        EN_REVISION: 12,       // Express repair workshop (shorter)
        EN_REPARACION: 72,     // Micro-soldering workshop (longer)
      };

      // 15 hours ago:
      // - Defaults: EN_REVISION (24h) -> false
      // - Custom: EN_REVISION (12h) -> true (15h >= 12h)
      const fifteenHoursAgo = new Date('2026-08-21T01:00:00.000Z').toISOString();
      expect(isTicketStale(fifteenHoursAgo, 'EN_REVISION')).toBe(false);
      expect(isTicketStale(fifteenHoursAgo, 'EN_REVISION', customThresholds)).toBe(true);

      // 50 hours ago:
      // - Defaults: EN_REPARACION (48h) -> true (50h >= 48h)
      // - Custom: EN_REPARACION (72h) -> false (50h < 72h)
      const fiftyHoursAgo = new Date('2026-08-19T14:00:00.000Z').toISOString();
      expect(isTicketStale(fiftyHoursAgo, 'EN_REPARACION')).toBe(true);
      expect(isTicketStale(fiftyHoursAgo, 'EN_REPARACION', customThresholds)).toBe(false);

      // Unconfigured status in customThresholds (e.g. EN_ESPERA_INGRESO) falls back to default 48h
      expect(isTicketStale(fiftyHoursAgo, 'EN_ESPERA_INGRESO', customThresholds)).toBe(true);
      const thirtyHoursAgo = new Date('2026-08-20T10:00:00.000Z').toISOString();
      expect(isTicketStale(thirtyHoursAgo, 'EN_ESPERA_INGRESO', customThresholds)).toBe(false);
    });
  });
});

