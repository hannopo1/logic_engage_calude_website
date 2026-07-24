"use client";

import { Coffee, Minus, Plus, ShoppingCart, Trash2 } from "lucide-react";
import Link from "next/link";

import { useCart } from "@/context/CartContext";
import { fmtEGP } from "@/lib/format";

/**
 * Renders the shopping cart page with empty-cart and populated-cart states.
 *
 * @returns The cart page interface
 */
export default function CartPage() {
  const { cart, update, remove } = useCart();

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-md space-y-4 rounded-2xl border border-line bg-white p-10 text-center">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-stone-100 text-muted">
          <ShoppingCart className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-ink">سلة التسوق</h1>
        <p className="text-muted">سلتك فارغة.</p>
        <Link
          href="/products"
          className="inline-block rounded-xl bg-brand-dark px-5 py-2.5 font-semibold text-white hover:bg-ink"
        >
          تصفّح المنتجات
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-ink">سلة التسوق</h1>
      <div className="divide-y divide-line rounded-2xl border border-line bg-white">
        {cart.items.map((it) => (
          <div key={it.id} className="flex items-center gap-4 p-4">
            <div className="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-xl bg-stone-100 text-stone-300">
              {it.product.image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={it.product.image} alt={it.product.name} className="h-full w-full object-cover" />
              ) : (
                <Coffee className="h-7 w-7" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate font-bold text-ink">{it.product.name}</p>
              <p className="text-sm text-muted">{fmtEGP(it.product.price)} للقطعة</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => update(it.product.id, it.quantity - 1)}
                aria-label="إنقاص"
                className="grid h-9 w-9 place-items-center rounded-lg border border-line text-ink hover:bg-stone-50"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-8 text-center font-semibold">{it.quantity}</span>
              <button
                onClick={() => update(it.product.id, it.quantity + 1)}
                aria-label="زيادة"
                className="grid h-9 w-9 place-items-center rounded-lg border border-line text-ink hover:bg-stone-50"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <div className="hidden w-24 text-left font-bold text-ink sm:block">
              {fmtEGP(it.line_total)}
            </div>
            <button
              onClick={() => remove(it.product.id)}
              aria-label="حذف"
              className="grid h-9 w-9 place-items-center rounded-lg text-red-600 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      <div className="flex flex-col items-stretch justify-between gap-3 rounded-2xl border border-line bg-white p-4 sm:flex-row sm:items-center">
        <span className="text-lg text-ink">
          الإجمالي: <span className="font-extrabold text-brand">{fmtEGP(cart.subtotal)}</span>
        </span>
        <Link
          href="/checkout"
          className="rounded-xl bg-brand-dark px-6 py-3 text-center font-semibold text-white hover:bg-ink"
        >
          إتمام الشراء
        </Link>
      </div>
    </div>
  );
}
