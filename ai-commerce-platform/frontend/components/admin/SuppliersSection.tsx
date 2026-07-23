"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Supplier } from "@/lib/types";

export default function SuppliersSection() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  useEffect(() => {
    api.adminSuppliers().then(setSuppliers).catch(() => {});
  }, []);

  const modeAr = (m: string) => (m === "api" ? "API آلي" : m === "assisted" ? "مساعَد" : "يدوي");

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-bold">الموردون ({suppliers.length})</h2>
      <div className="grid gap-2 md:grid-cols-2">
        {suppliers.map((s) => (
          <div key={s.id} className="rounded-lg border border-stone-200 bg-white p-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">
                {s.name}{" "}
                <span className="text-xs text-stone-400">
                  ({s.kind === "classifieds" ? "إعلانات أفراد" : "متجر"})
                </span>
              </span>
              <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs">{modeAr(s.mode)}</span>
            </div>
            {s.notes && <p className="mt-2 text-xs text-stone-500">{s.notes}</p>}
          </div>
        ))}
      </div>
      <p className="text-xs text-stone-400">
        الوضع «مساعَد» = الوكيل يجهّز الشراء والمشغّل ينفّذه. «API آلي» يتطلب حساب/مفاتيح رسمية للمورد.
      </p>
    </div>
  );
}
