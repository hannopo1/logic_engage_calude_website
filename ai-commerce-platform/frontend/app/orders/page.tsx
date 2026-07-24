"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtDate, fmtEGP } from "@/lib/format";
import type { Order } from "@/lib/types";

const STATUS_AR: Record<string, string> = {
  pending: "قيد المراجعة",
  processing: "جارٍ التجهيز",
  shipped: "تم الشحن",
  completed: "تم التسليم",
  cancelled: "ملغي",
};

/**
 * Displays the current user's orders, with loading, empty, and login-required states.
 */
export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [needLogin, setNeedLogin] = useState(false);

  useEffect(() => {
    api
      .myOrders()
      .then(setOrders)
      .catch(() => setNeedLogin(true));
  }, []);

  if (needLogin) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-extrabold text-ink">طلباتي</h1>
        <p className="text-muted">سجّل الدخول لعرض طلباتك.</p>
        <Link href="/login" className="font-semibold text-brand hover:underline">
          تسجيل الدخول
        </Link>
      </div>
    );
  }

  if (orders === null) return <p className="text-muted">جارٍ التحميل…</p>;

  if (orders.length === 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-extrabold text-ink">طلباتي</h1>
        <p className="text-muted">لا توجد طلبات بعد.</p>
        <Link href="/products" className="font-semibold text-brand hover:underline">
          ابدأ التسوّق
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-extrabold text-ink">طلباتي</h1>
      <div className="divide-y divide-line rounded-2xl border border-line bg-white">
        {orders.map((o) => (
          <Link
            key={o.id}
            href={`/orders/${o.id}`}
            className="flex items-center justify-between p-4 transition hover:bg-stone-50"
          >
            <div>
              <p className="font-bold text-ink">طلب #{o.id}</p>
              <p className="text-sm text-muted">{fmtDate(o.created_at)}</p>
            </div>
            <div className="text-left">
              <p className="font-extrabold text-brand">{fmtEGP(o.total_amount)}</p>
              <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-muted">
                {STATUS_AR[o.status] || o.status}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
