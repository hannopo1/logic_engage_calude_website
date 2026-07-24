"use client";

import { ArrowRight, Check } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtDate, fmtEGP } from "@/lib/format";
import type { Order, TimelineStep } from "@/lib/types";

/**
 * Displays the tracking timeline, summary, shipping details, and payment method for an order.
 *
 * @param params - Route parameters containing the order identifier.
 * @returns The order tracking page content.
 */
export default function OrderTrackingPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  const [order, setOrder] = useState<Order | null>(null);
  const [timeline, setTimeline] = useState<TimelineStep[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.order(id), api.orderTimeline(id)])
      .then(([o, t]) => {
        setOrder(o);
        setTimeline(t);
      })
      .catch((e) => setError((e as Error).message));
  }, [id]);

  if (error)
    return (
      <div className="space-y-3">
        <p className="text-muted">{error}</p>
        <Link href="/orders" className="font-semibold text-brand hover:underline">
          العودة لطلباتي
        </Link>
      </div>
    );
  if (!order) return <p className="text-muted">جارٍ التحميل…</p>;

  const discount = order.discount_amount ? Number(order.discount_amount) : 0;

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <Link href="/orders" className="inline-flex items-center gap-1 text-sm font-semibold text-brand hover:underline">
          <ArrowRight className="h-4 w-4" /> كل الطلبات
        </Link>
        <h1 className="mt-2 text-2xl font-extrabold text-ink">تتبّع الطلب #{order.id}</h1>
        <p className="text-sm text-muted">{fmtDate(order.created_at)}</p>
      </div>

      {/* Timeline stepper */}
      <div className="rounded-2xl border border-line bg-white p-6">
        <ol className="space-y-5">
          {timeline.map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span
                className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs ${
                  step.done ? "bg-green-600 text-white" : "border border-line text-stone-400"
                }`}
              >
                {step.done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </span>
              <div>
                <p className={step.done ? "font-semibold text-ink" : "text-stone-400"}>{step.label}</p>
                {step.at && <p className="text-xs text-muted">{fmtDate(step.at)}</p>}
              </div>
            </li>
          ))}
        </ol>
      </div>

      {/* Order summary */}
      <div className="overflow-hidden rounded-2xl border border-line bg-white">
        <div className="border-b border-line p-4">
          <h2 className="font-bold text-ink">تفاصيل الطلب</h2>
        </div>
        <div className="divide-y divide-line">
          {order.items.map((it, i) => (
            <div key={i} className="flex items-center justify-between p-4 text-sm">
              <span className="text-ink">
                {it.product_name} × {it.quantity}
              </span>
              <span className="font-medium text-ink">{fmtEGP(it.total_price)}</span>
            </div>
          ))}
        </div>
        {discount > 0 && (
          <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm text-green-700">
            <span>خصم {order.coupon_code ? `(${order.coupon_code})` : ""}</span>
            <span>− {fmtEGP(order.discount_amount!)}</span>
          </div>
        )}
        <div className="flex items-center justify-between border-t border-line p-4">
          <span className="text-ink">الإجمالي</span>
          <span className="font-extrabold text-brand">{fmtEGP(order.total_amount)}</span>
        </div>
      </div>

      <div className="rounded-2xl bg-stone-100 p-4 text-sm text-muted">
        <p>عنوان الشحن: {order.shipping_address}</p>
        <p className="mt-1">
          طريقة الدفع: {order.payment_method === "cod" ? "الدفع عند الاستلام" : "بطاقة"}
        </p>
      </div>
    </div>
  );
}
