"use client";

import type { ReactNode } from "react";

export function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4">
      <p className="text-xs text-stone-500">{label}</p>
      <p className="mt-1 text-lg font-bold text-brand">{value}</p>
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
      className={`rounded-md px-4 py-2 text-sm font-semibold disabled:opacity-50 ${
        variant === "solid"
          ? "bg-brand text-white hover:bg-brand-dark"
          : "border border-stone-300 text-stone-600 hover:bg-stone-50"
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
  "w-full rounded-md border border-stone-300 p-2.5 text-sm outline-none focus:border-brand";
