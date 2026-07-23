"use client";

import { useEffect, useState } from "react";

import AnalyticsSection from "@/components/admin/AnalyticsSection";
import CustomersSection from "@/components/admin/CustomersSection";
import OrdersSection from "@/components/admin/OrdersSection";
import ProductsSection from "@/components/admin/ProductsSection";
import SuppliersSection from "@/components/admin/SuppliersSection";
import { api } from "@/lib/api";

type Section = "orders" | "products" | "customers" | "analytics" | "suppliers";

const NAV: { key: Section; label: string }[] = [
  { key: "orders", label: "الطلبات والتوريد" },
  { key: "products", label: "المنتجات" },
  { key: "customers", label: "العملاء" },
  { key: "analytics", label: "التحليلات" },
  { key: "suppliers", label: "الموردون" },
];

export default function AdminPage() {
  const [ok, setOk] = useState<boolean | null>(null);
  const [section, setSection] = useState<Section>("orders");

  useEffect(() => {
    // Any admin-only call verifies the operator role.
    api
      .adminDashboard()
      .then(() => setOk(true))
      .catch(() => setOk(false));
  }, []);

  if (ok === false)
    return (
      <div className="space-y-3">
        <h1 className="text-2xl font-bold">لوحة الإدارة</h1>
        <p className="text-stone-500">
          هذه الصفحة للمشغّلين فقط. سجّل الدخول بحساب إداري (admin@example.com / admin1234).
        </p>
        <a href="/login" className="text-brand underline">
          تسجيل الدخول
        </a>
      </div>
    );
  if (ok === null) return <p className="text-stone-500">جارٍ التحميل…</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">لوحة تشغيل المتجر</h1>

      <nav className="flex flex-wrap gap-2 border-b border-stone-200 pb-3">
        {NAV.map((n) => (
          <button
            key={n.key}
            onClick={() => setSection(n.key)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium ${
              section === n.key ? "bg-brand text-white" : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            {n.label}
          </button>
        ))}
      </nav>

      {section === "orders" && <OrdersSection />}
      {section === "products" && <ProductsSection />}
      {section === "customers" && <CustomersSection />}
      {section === "analytics" && <AnalyticsSection />}
      {section === "suppliers" && <SuppliersSection />}
    </div>
  );
}
