"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtDate, fmtEGP } from "@/lib/format";
import type { Order, TimelineStep } from "@/lib/types";

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
        <p className="text-stone-500">{error}</p>
        <Link href="/orders" className="text-brand underline">
          العودة لطلباتي
        </Link>
      </div>
    );
  if (!order) return <p className="text-stone-500">جارٍ التحميل…</p>;

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <div>
        <Link href="/orders" className="text-sm text-brand underline">
          ← كل الطلبات
        </Link>
        <h1 className="mt-2 text-2xl font-bold">تتبّع الطلب #{order.id}</h1>
        <p className="text-sm text-stone-500">{fmtDate(order.created_at)}</p>
      </div>

      {/* Timeline stepper */}
      <div className="rounded-lg border border-stone-200 bg-white p-6">
        <ol className="space-y-5">
          {timeline.map((step, i) => (
            <li key={i} className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs ${
                  step.done ? "bg-green-600 text-white" : "border border-stone-300 text-stone-400"
                }`}
              >
                {step.done ? "✓" : i + 1}
              </span>
              <div>
                <p className={step.done ? "font-medium" : "text-stone-400"}>{step.label}</p>
                {step.at && <p className="text-xs text-stone-400">{fmtDate(step.at)}</p>}
              </div>
            </li>
          ))}
        </ol>
      </div>

      {/* Order summary */}
      <div className="rounded-lg border border-stone-200 bg-white">
        <div className="border-b border-stone-100 p-4">
          <h2 className="font-semibold">تفاصيل الطلب</h2>
        </div>
        <div className="divide-y divide-stone-100">
          {order.items.map((it, i) => (
            <div key={i} className="flex items-center justify-between p-4 text-sm">
              <span>
                {it.product_name} × {it.quantity}
              </span>
              <span className="font-medium">{fmtEGP(it.total_price)}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-between border-t border-stone-200 p-4">
          <span>الإجمالي</span>
          <span className="font-bold text-brand">{fmtEGP(order.total_amount)}</span>
        </div>
      </div>

      <div className="rounded-lg bg-stone-100 p-4 text-sm text-stone-600">
        <p>عنوان الشحن: {order.shipping_address}</p>
        <p className="mt-1">
          طريقة الدفع: {order.payment_method === "cod" ? "الدفع عند الاستلام" : "بطاقة"}
        </p>
      </div>
    </div>
  );
}
