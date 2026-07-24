"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtDate, fmtEGP } from "@/lib/format";
import type { Customer } from "@/lib/types";

/**
 * Displays the administrative customer list with loading and empty states.
 */
export default function CustomersSection() {
  const [customers, setCustomers] = useState<Customer[] | null>(null);

  useEffect(() => {
    api.adminCustomers().then(setCustomers).catch(() => setCustomers([]));
  }, []);

  if (customers === null) return <p className="text-stone-500">جارٍ التحميل…</p>;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold">العملاء ({customers.length})</h2>
      {customers.length === 0 ? (
        <p className="text-stone-500">لا يوجد عملاء مسجّلون بعد.</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-stone-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 text-stone-500">
              <tr>
                <th className="p-3 text-right">العميل</th>
                <th className="p-3 text-right">البريد</th>
                <th className="p-3 text-center">الطلبات</th>
                <th className="p-3 text-center">إجمالي الإنفاق</th>
                <th className="p-3 text-center">مسجّل منذ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {customers.map((c) => (
                <tr key={c.id} className="hover:bg-stone-50">
                  <td className="p-3">{[c.first_name, c.last_name].filter(Boolean).join(" ") || "—"}</td>
                  <td className="p-3">{c.email}</td>
                  <td className="p-3 text-center">{c.order_count}</td>
                  <td className="p-3 text-center font-medium text-brand">{fmtEGP(c.total_spent)}</td>
                  <td className="p-3 text-center text-xs text-stone-400">{fmtDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
