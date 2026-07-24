/**
 * Formats a value as Egyptian pounds using the Arabic-Egypt locale.
 *
 * @param value - The numeric value or numeric string to format
 * @returns The formatted value with the `ج.م` currency label, or the original value with the label if it cannot be parsed
 */
export function fmtEGP(value: string | number): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return `${value} ج.م`;
  return `${n.toLocaleString("ar-EG", { maximumFractionDigits: 2 })} ج.م`;
}

/**
 * Formats a date-time string for the Egyptian Arabic locale.
 *
 * @param iso - The date-time string to format
 * @returns The localized date-time string, or the original input if formatting fails
 */
export function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ar-EG", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}
