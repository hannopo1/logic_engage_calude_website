"use client";

import { Coffee, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Stars } from "@/components/Stars";
import { useCart } from "@/context/CartContext";
import { fmtEGP } from "@/lib/format";
import type { Product } from "@/lib/types";

export default function ProductCard({ product }: { product: Product }) {
  const { add } = useCart();
  const [busy, setBusy] = useState(false);
  const soldOut = product.stock_qty <= 0;
  const count = product.rating_count ?? 0;

  const onAdd = async () => {
    setBusy(true);
    try {
      await add(product.id, 1);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="group flex flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-card transition hover:-translate-y-0.5 hover:shadow-lift">
      <Link href={`/product/${product.slug}`} className="block">
        <div className="relative aspect-square overflow-hidden bg-gradient-to-br from-stone-100 to-stone-200">
          {product.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={product.image}
              alt={product.name}
              className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="grid h-full w-full place-items-center text-stone-300">
              <Coffee className="h-14 w-14" />
            </div>
          )}
          {soldOut && (
            <span className="absolute right-2 top-2 rounded-full bg-ink/80 px-2 py-1 text-xs font-medium text-white">
              غير متوفر
            </span>
          )}
        </div>
      </Link>

      <div className="flex flex-1 flex-col p-4">
        <Link href={`/product/${product.slug}`}>
          <h3 className="line-clamp-2 min-h-[2.75rem] font-bold leading-snug text-ink hover:text-brand">
            {product.name}
          </h3>
        </Link>

        <div className="mt-1 flex items-center gap-1.5 text-xs text-muted">
          {count > 0 ? (
            <>
              <Stars value={product.rating_avg ?? 0} size={14} />
              <span>({count})</span>
            </>
          ) : (
            <span className="text-stone-400">لا توجد تقييمات بعد</span>
          )}
        </div>

        <p className="mt-2 text-lg font-extrabold text-brand">{fmtEGP(product.price)}</p>

        <button
          onClick={onAdd}
          disabled={busy || soldOut}
          className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl bg-brand-dark py-2.5 text-sm font-semibold text-white transition hover:bg-ink disabled:opacity-50"
        >
          <Plus className="h-4 w-4" />
          {soldOut ? "غير متوفر" : busy ? "جارٍ الإضافة…" : "أضف للسلة"}
        </button>
      </div>
    </div>
  );
}
