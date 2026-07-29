/**
 * Utility functions for masking Personally Identifiable Information (PII).
 * Used primarily on dashboard summaries to prevent shoulder surfing.
 */

/**
 * Masks a phone number by keeping the first two characters visible
 * and replacing subsequent digits with 'x'.
 * @param {string} phone - The raw phone number string.
 * @returns {string} The masked phone number.
 */
export function maskPhone(phone) {
  if (!phone || typeof phone !== "string") return phone || "";
  const str = phone.trim();
  if (str.length <= 2) return "xx";

  const prefix = str.slice(0, 2);
  return `${prefix}${"x".repeat(str.length - 2)}`;
}

/**
 * Masks an email address by replacing intermediate characters in the username
 * with 'x', while keeping the domain completely visible.
 * @param {string} email - The raw email address string.
 * @returns {string} The masked email address.
 */
export function maskEmail(email) {
  if (!email || typeof email !== "string") return email || "";
  const str = email.trim();
  const parts = str.split("@");
  if (parts.length !== 2) return str;

  const [user, domain] = parts;
  if (user.length <= 2) {
    return `${user[0] || "x"}x@${domain}`;
  }
  if (user.length <= 4) {
    return `${user.slice(0, 2)}xx@${domain}`;
  }

  const prefix = user.slice(0, 2);
  const suffix = user.slice(-1);
  const maskedCount = Math.min(6, Math.max(3, user.length - 3));

  return `${prefix}${"x".repeat(maskedCount)}${suffix}@${domain}`;
}

/**
 * Masks a tracking code / guía by showing only the first two characters
 * followed by masked 'x' characters (e.g. "e0xxxxxx...").
 * @param {string} code - The raw tracking token / code string.
 * @returns {string} The masked tracking code.
 */
export function maskTrackingCode(code) {
  if (!code || typeof code !== "string") return code || "";
  const str = code.trim();
  if (str.length <= 2) return `${str}xx...`;
  const prefix = str.slice(0, 2);
  return `${prefix}xxxxxx...`;
}
