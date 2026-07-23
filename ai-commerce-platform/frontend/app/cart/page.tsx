"use client";

import Link from "next/link";

import { useCart } from "@/context/CartContext";
import { fmtEGP } from "@/lib/format";

export default function CartPage() {
  const { cart, update, remove } = useCart();

  if (!cart || cart.items.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">سلة التسوق</h1>
        <p className="text-stone-500">سلتك فارغة.</p>
        <Link href="/products" className="text-brand underline">
          تصفّح المنتجات
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">سلة التسوق</h1>
      <div className="divide-y divide-stone-200 rounded-lg border border-stone-200 bg-white">
        {cart.items.map((it) => (
          <div key={it.id} className="flex items-center gap-4 p-4">
            <div className="flex h-16 w-16 items-center justify-center rounded bg-stone-100 text-2xl">
              ☕
            </div>
            <div className="flex-1">
              <p className="font-medium">{it.product.name}</p>
              <p className="text-sm text-stone-500">{fmtEGP(it.product.price)} للقطعة</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => update(it.product.id, it.quantity - 1)}
                className="h-8 w-8 rounded border border-stone-300"
              >
                −
              </button>
              <span className="w-8 text-center">{it.quantity}</span>
              <button
                onClick={() => update(it.product.id, it.quantity + 1)}
                className="h-8 w-8 rounded border border-stone-300"
              >
                +
              </button>
            </div>
            <div className="w-24 text-left font-semibold">{fmtEGP(it.line_total)}</div>
            <button
              onClick={() => remove(it.product.id)}
              className="text-sm text-red-600 hover:underline"
            >
              حذف
            </button>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-lg">
          الإجمالي:{" "}
          <span className="font-bold text-brand">{fmtEGP(cart.subtotal)}</span>
        </span>
        <Link
          href="/checkout"
          className="rounded-md bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark"
        >
          إتمام الشراء
        </Link>
      </div>
    </div>
  );
}
