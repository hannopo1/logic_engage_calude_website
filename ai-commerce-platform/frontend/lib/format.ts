/** Currency formatting for the Egyptian market. */
export function fmtEGP(value: string | number): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return `${value} ج.م`;
  return `${n.toLocaleString("ar-EG", { maximumFractionDigits: 2 })} ج.م`;
}

/** Short Arabic date-time. */
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
