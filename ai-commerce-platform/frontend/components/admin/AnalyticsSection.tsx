"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Analytics } from "@/lib/types";
import { Stat } from "./ui";

export default function AnalyticsSection() {
  const [a, setA] = useState<Analytics | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    api.adminAnalytics(days).then(setA).catch(() => {});
  }, [days]);

  if (!a) return <p className="text-stone-500">جارٍ التحميل…</p>;

  const maxFunnel = Math.max(1, ...a.funnel.map((f) => f.count));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">تحليلات الزوّار</h2>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded-md border border-stone-300 p-2 text-sm"
        >
          <option value={7}>آخر 7 أيام</option>
          <option value={30}>آخر 30 يوم</option>
          <option value={90}>آخر 90 يوم</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="زوّار مميّزون" value={String(a.unique_visitors)} />
        <Stat label="مشاهدات المنتجات" value={String(a.product_views)} />
        <Stat label="عمليات بحث" value={String(a.searches)} />
        <Stat label="معدل التحويل" value={`${a.conversion_rate}%`} />
      </div>

      {/* Funnel */}
      <div className="rounded-lg border border-stone-200 bg-white p-4">
        <h3 className="mb-3 font-semibold">مسار الشراء (Funnel)</h3>
        <div className="space-y-2">
          {a.funnel.map((f) => (
            <div key={f.key} className="flex items-center gap-3">
              <span className="w-28 shrink-0 text-sm text-stone-600">{f.label}</span>
              <div className="h-6 flex-1 overflow-hidden rounded bg-stone-100">
                <div
                  className="flex h-6 items-center justify-end rounded bg-brand px-2 text-xs font-medium text-white"
                  style={{ width: `${Math.max(6, (f.count / maxFunnel) * 100)}%` }}
                >
                  {f.count}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-stone-200 bg-white p-4">
          <h3 className="mb-3 font-semibold">أكثر المنتجات مشاهدة</h3>
          {a.top_products.length === 0 ? (
            <p className="text-sm text-stone-500">لا بيانات بعد.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {a.top_products.map((t, i) => (
                <li key={i} className="flex justify-between">
                  <span>{t.label}</span>
                  <span className="font-medium text-brand">{t.count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="rounded-lg border border-stone-200 bg-white p-4">
          <h3 className="mb-3 font-semibold">أكثر عبارات البحث</h3>
          {a.top_searches.length === 0 ? (
            <p className="text-sm text-stone-500">لا بيانات بعد.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {a.top_searches.map((t, i) => (
                <li key={i} className="flex justify-between">
                  <span>{t.label}</span>
                  <span className="font-medium text-brand">{t.count}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
