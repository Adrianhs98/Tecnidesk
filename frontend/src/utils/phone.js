/**
 * Phone utilities for Ecuadorian mobile numbers.
 */

/**
 * Sanitizes phone input by removing spaces, dashes, parentheses and periods,
 * while preserving a leading '+' if present.
 *
 * @param {string|null|undefined} phone
 * @returns {string}
 */
export function cleanPhoneNumber(phone) {
  if (!phone || typeof phone !== 'string') return '';
  const trimmed = phone.trim();
  if (trimmed.startsWith('+')) {
    return '+' + trimmed.slice(1).replace(/\D/g, '');
  }
  return trimmed.replace(/\D/g, '');
}

/**
 * Validates whether the given phone string matches Ecuadorian mobile phone formats:
 * - National format: exactly 10 digits starting with '09' (e.g., 0991234567)
 * - International format: +5939XXXXXXXX or 5939XXXXXXXX (total 12 digits excluding +)
 *
 * Returns true if the phone is null, undefined, or empty (when optional).
 *
 * @param {string|null|undefined} phone
 * @returns {boolean}
 */
export function isValidMobilePhone(phone) {
  if (phone === null || phone === undefined) return true;
  if (typeof phone !== 'string') return false;
  if (phone.trim() === '') return true;

  const cleaned = cleanPhoneNumber(phone);

  // National mobile: 09 followed by 8 digits (10 digits total)
  const isNationalMobile = /^09\d{8}$/.test(cleaned);

  // International mobile: +5939 or 5939 followed by 8 digits
  const isInternationalMobile = /^(?:\+5939|5939)\d{8}$/.test(cleaned);

  return isNationalMobile || isInternationalMobile;
}
