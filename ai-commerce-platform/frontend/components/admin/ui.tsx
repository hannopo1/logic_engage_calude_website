"use client";

import type { ReactNode } from "react";

export function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-white p-4 shadow-card">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-lg font-extrabold text-brand">{value}</p>
    </div>
  );
}

export function Btn({
  children,
  onClick,
  variant = "solid",
  type = "button",
  disabled,
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "solid" | "ghost";
  type?: "button" | "submit";
  disabled?: boolean;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-xl px-4 py-2 text-sm font-semibold disabled:opacity-50 ${
        variant === "solid"
          ? "bg-brand-dark text-white hover:bg-ink"
          : "border border-line text-muted hover:bg-stone-50"
      }`}
    >
      {children}
    </button>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

export const inputCls =
  "w-full rounded-xl border border-line p-2.5 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20";
