"use client";

import { Check } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCart } from "@/context/CartContext";
import { api } from "@/lib/api";
import { fmtEGP } from "@/lib/format";
import type { Order } from "@/lib/types";

/**
 * Renders the checkout form and, after a successful submission, the order confirmation view.
 *
 * @returns The checkout form or order confirmation interface
 */
export default function CheckoutPage() {
  const { cart, refresh } = useCart();
  const router = useRouter();
  const [address, setAddress] = useState("");
  const [method, setMethod] = useState<"cod" | "gateway">("cod");
  const [busy, setBusy] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");

  // Coupon state
  const [couponInput, setCouponInput] = useState("");
  const [coupon, setCoupon] = useState<{ code: string; discount: string; new_total: string } | null>(null);
  const [couponMsg, setCouponMsg] = useState("");

  const applyCoupon = async () => {
    const code = couponInput.trim();
    if (!code || !cart) return;
    setCouponMsg("");
    try {
      const res = await api.validateCoupon(code, cart.subtotal);
      setCoupon(res);
      setCouponMsg(`تم تطبيق الكود — خصم ${fmtEGP(res.discount)}`);
    } catch (err) {
      setCoupon(null);
      setCouponMsg((err as Error).message);
    }
  };
  const clearCoupon = () => {
    setCoupon(null);
    setCouponInput("");
    setCouponMsg("");
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    api.track({ event_type: "begin_checkout" });
    try {
      const o = await api.checkoutWith(address, method, coupon?.code);
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
    const hasDiscount = order.discount_amount && Number(order.discount_amount) > 0;
    return (
      <div className="mx-auto max-w-md space-y-4 rounded-2xl border border-line bg-white p-8 text-center shadow-card">
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-green-100 text-green-700">
          <Check className="h-7 w-7" />
        </div>
        <h1 className="text-2xl font-extrabold text-green-700">تم تأكيد الطلب</h1>
        {hasDiscount && (
          <p className="text-sm text-green-700">
            كود الخصم <strong>{order.coupon_code}</strong> — وفّرت{" "}
            <strong>{fmtEGP(order.discount_amount!)}</strong>
          </p>
        )}
        <p>
          طلب رقم <strong>#{order.id}</strong> — الإجمالي{" "}
          <strong>{fmtEGP(order.total_amount)}</strong>
        </p>
        <p className="text-muted">الدفع عند الاستلام — سنجهّز طلبك ونشحنه لعنوانك.</p>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => router.push(`/orders/${order.id}`)}
            className="rounded-xl bg-brand-dark px-6 py-3 font-semibold text-white hover:bg-ink"
          >
            تتبّع الطلب
          </button>
          <button
            onClick={() => router.push("/products")}
            className="rounded-xl border border-line px-6 py-3 font-semibold text-ink hover:bg-stone-50"
          >
            متابعة التسوّق
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <h1 className="text-2xl font-extrabold text-ink">إتمام الشراء</h1>
      {cart && (
        <p className="text-muted">
          {cart.item_count} منتج — الإجمالي{" "}
          <span className="font-extrabold text-brand">{fmtEGP(cart.subtotal)}</span>
        </p>
      )}
      <form onSubmit={submit} className="space-y-4 rounded-2xl border border-line bg-white p-5 shadow-card">
        <div>
          <label className="mb-1 block text-sm font-medium text-ink">عنوان الشحن</label>
          <textarea
            required
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="المحافظة، المدينة، الشارع، رقم المبنى…"
            rows={3}
            className="w-full rounded-xl border border-line p-3 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink">طريقة الدفع</label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 rounded-xl border border-line p-3">
              <input
                type="radio"
                name="method"
                checked={method === "cod"}
                onChange={() => setMethod("cod")}
              />
              <span className="text-ink">الدفع عند الاستلام (كاش)</span>
            </label>
            <label className="flex items-center gap-2 rounded-xl border border-line p-3 text-stone-400">
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

        <div>
          <label className="mb-1 block text-sm font-medium text-ink">كود الخصم (اختياري)</label>
          {coupon ? (
            <div className="flex items-center justify-between rounded-xl border border-green-300 bg-green-50 p-3">
              <span className="text-sm text-green-800">
                <strong>{coupon.code}</strong> — خصم {fmtEGP(coupon.discount)}
              </span>
              <button
                type="button"
                onClick={clearCoupon}
                className="text-sm font-medium text-red-600 hover:underline"
              >
                إزالة
              </button>
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                value={couponInput}
                onChange={(e) => setCouponInput(e.target.value)}
                placeholder="مثال: WELCOME10"
                className="flex-1 rounded-xl border border-line p-3 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
              />
              <button
                type="button"
                onClick={applyCoupon}
                disabled={!couponInput.trim() || !cart}
                className="rounded-xl border border-brand px-4 font-semibold text-brand hover:bg-brand hover:text-white disabled:opacity-50"
              >
                تطبيق
              </button>
            </div>
          )}
          {couponMsg && (
            <p className={`mt-1 text-sm ${coupon ? "text-green-700" : "text-red-600"}`}>{couponMsg}</p>
          )}
        </div>

        {cart && coupon && (
          <div className="space-y-1 rounded-xl bg-stone-50 p-3 text-sm">
            <div className="flex justify-between">
              <span>الإجمالي الفرعي</span>
              <span>{fmtEGP(cart.subtotal)}</span>
            </div>
            <div className="flex justify-between text-green-700">
              <span>الخصم</span>
              <span>− {fmtEGP(coupon.discount)}</span>
            </div>
            <div className="flex justify-between border-t border-line pt-1 font-bold">
              <span>الإجمالي بعد الخصم</span>
              <span className="text-brand">{fmtEGP(coupon.new_total)}</span>
            </div>
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy || !cart || cart.items.length === 0}
          className="w-full rounded-xl bg-brand-dark py-3 font-semibold text-white hover:bg-ink disabled:opacity-50"
        >
          {busy ? "جارٍ تأكيد الطلب…" : "تأكيد الطلب"}
        </button>
      </form>
      <p className="text-center text-xs text-muted">
        الدفع الإلكتروني يُفعّل عند ربط بوابة دفع (Paymob/Stripe). حالياً الدفع عند الاستلام.
      </p>
    </div>
  );
}
