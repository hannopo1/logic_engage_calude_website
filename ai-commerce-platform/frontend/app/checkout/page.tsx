"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCart } from "@/context/CartContext";
import { api } from "@/lib/api";
import { fmtEGP } from "@/lib/format";
import type { Order } from "@/lib/types";

export default function CheckoutPage() {
  const { cart, refresh } = useCart();
  const router = useRouter();
  const [address, setAddress] = useState("");
  const [method, setMethod] = useState<"cod" | "gateway">("cod");
  const [busy, setBusy] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    api.track({ event_type: "begin_checkout" });
    try {
      const o = await api.checkoutWith(address, method);
      api.track({ event_type: "purchase", path: `/orders/${o.id}` });
      setOrder(o);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (order) {
    return (
      <div className="space-y-4 text-center">
        <h1 className="text-2xl font-bold text-green-700">تم تأكيد الطلب ✓</h1>
        <p>
          طلب رقم <strong>#{order.id}</strong> — الإجمالي{" "}
          <strong>{fmtEGP(order.total_amount)}</strong>
        </p>
        <p className="text-stone-500">الدفع عند الاستلام — سنجهّز طلبك ونشحنه لعنوانك.</p>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => router.push(`/orders/${order.id}`)}
            className="rounded-md bg-brand px-6 py-3 font-semibold text-white"
          >
            تتبّع الطلب
          </button>
          <button
            onClick={() => router.push("/products")}
            className="rounded-md border border-stone-300 px-6 py-3 font-semibold"
          >
            متابعة التسوّق
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <h1 className="text-2xl font-bold">إتمام الشراء</h1>
      {cart && (
        <p className="text-stone-600">
          {cart.item_count} منتج — الإجمالي{" "}
          <span className="font-bold text-brand">{fmtEGP(cart.subtotal)}</span>
        </p>
      )}
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium">عنوان الشحن</label>
          <textarea
            required
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="المحافظة، المدينة، الشارع، رقم المبنى…"
            rows={3}
            className="w-full rounded-md border border-stone-300 p-3 outline-none focus:border-brand"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">طريقة الدفع</label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 rounded-md border border-stone-300 p-3">
              <input
                type="radio"
                name="method"
                checked={method === "cod"}
                onChange={() => setMethod("cod")}
              />
              <span>الدفع عند الاستلام (كاش)</span>
            </label>
            <label className="flex items-center gap-2 rounded-md border border-stone-200 p-3 text-stone-400">
              <input
                type="radio"
                name="method"
                checked={method === "gateway"}
                onChange={() => setMethod("gateway")}
              />
              <span>بطاقة / محفظة إلكترونية (قريباً)</span>
            </label>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy || !cart || cart.items.length === 0}
          className="w-full rounded-md bg-brand py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {busy ? "جارٍ تأكيد الطلب…" : "تأكيد الطلب"}
        </button>
      </form>
      <p className="text-center text-xs text-stone-400">
        الدفع الإلكتروني يُفعّل عند ربط بوابة دفع (Paymob/Stripe). حالياً الدفع عند الاستلام.
      </p>
    </div>
  );
}
