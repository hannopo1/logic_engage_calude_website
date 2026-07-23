"use client";

import Link from "next/link";
import { useState } from "react";

import { useCart } from "@/context/CartContext";
import type { Product } from "@/lib/types";

export default function ProductCard({ product }: { product: Product }) {
  const { add } = useCart();
  const [busy, setBusy] = useState(false);

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
    <div className="flex flex-col overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm transition hover:shadow-md">
      <Link href={`/product/${product.slug}`} className="block">
        <div className="flex h-40 items-center justify-center bg-stone-100 text-4xl">
          ☕
        </div>
        <div className="p-4">
          <h3 className="line-clamp-2 min-h-[2.5rem] font-medium">{product.name}</h3>
          <p className="mt-1 text-lg font-bold text-brand">${product.price}</p>
        </div>
      </Link>
      <div className="mt-auto p-4 pt-0">
        <button
          onClick={onAdd}
          disabled={busy || product.stock_qty <= 0}
          className="w-full rounded-md bg-brand py-2 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:opacity-50"
        >
          {product.stock_qty <= 0 ? "Out of stock" : busy ? "Adding…" : "Add to cart"}
        </button>
      </div>
    </div>
  );
}
