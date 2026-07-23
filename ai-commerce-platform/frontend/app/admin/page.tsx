"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtEGP } from "@/lib/format";
import type { ApproveResult, Dashboard, PurchaseOrder, Supplier } from "@/lib/types";

const STATUS_AR: Record<string, string> = {
  pending_sourcing: "بانتظار التوريد",
  awaiting_approval: "بانتظار الموافقة",
  purchasing: "جارٍ الشراء",
  purchased: "تم الشراء",
  shipped: "تم الشحن",
  delivered: "تم التسليم",
  failed: "فشل",
  cancelled: "ملغي",
};

const TABS: string[] = [
  "awaiting_approval",
  "pending_sourcing",
  "purchasing",
  "purchased",
  "shipped",
  "delivered",
];

export default function AdminPage() {
  const [ok, setOk] = useState<boolean | null>(null);
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [tab, setTab] = useState<string>("awaiting_approval");
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [pkg, setPkg] = useState<ApproveResult | null>(null);
  const [msg, setMsg] = useState("");

  const loadTab = useCallback(async (t: string) => {
    setPos(await api.adminPurchaseOrders(t));
  }, []);

  const refresh = useCallback(async () => {
    setDash(await api.adminDashboard());
    await loadTab(tab);
  }, [tab, loadTab]);

  useEffect(() => {
    api
      .adminDashboard()
      .then(async (d) => {
        setDash(d);
        setSuppliers(await api.adminSuppliers());
        setOk(true);
      })
      .catch(() => setOk(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (ok) loadTab(tab);
  }, [tab, ok, loadTab]);

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

  const flash = (t: string) => {
    setMsg(t);
    setTimeout(() => setMsg(""), 4000);
  };

  const onApprove = async (po: PurchaseOrder) => {
    try {
      const res = await api.adminApprove(po.id);
      setPkg(res);
      flash(
        res.result === "purchased"
          ? "تم تنفيذ الشراء آلياً (وضع المحاكاة)."
          : "تمت الموافقة — حزمة الشراء جاهزة للمشغّل.",
      );
      await refresh();
    } catch (e) {
      flash((e as Error).message);
    }
  };

  const onReject = async (po: PurchaseOrder) => {
    const note = prompt("سبب الرفض؟");
    if (!note) return;
    await api.adminReject(po.id, note, confirm("إلغاء البند نهائياً؟ (إلغاء = موافق)"));
    flash("تم رفض أمر الشراء.");
    await refresh();
  };

  const onMarkPurchased = async (po: PurchaseOrder) => {
    const ref = prompt("مرجع طلب المورد؟");
    if (!ref) return;
    const cost = prompt("التكلفة الفعلية (اختياري)؟") || undefined;
    await api.adminMarkPurchased(po.id, ref, cost);
    flash("تم تسجيل الشراء.");
    await refresh();
  };

  const onShip = async (po: PurchaseOrder) => {
    const track = prompt("رقم التتبع؟");
    if (!track) return;
    const carrier = prompt("شركة الشحن (اختياري)؟") || undefined;
    await api.adminShip(po.id, track, carrier);
    flash("تم تسجيل الشحن.");
    await refresh();
  };

  const onDeliver = async (po: PurchaseOrder) => {
    await api.adminDeliver(po.id);
    flash("تم تأكيد التسليم.");
    await refresh();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">لوحة تشغيل الدروب شيبينج</h1>

      {/* Stats */}
      {dash && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Stat label="طلبات اليوم" value={String(dash.orders_today)} />
          <Stat label="إجمالي الإيراد" value={fmtEGP(dash.revenue_total)} />
          <Stat label="تكلفة مفتوحة" value={fmtEGP(dash.expected_cost_open)} />
          <Stat
            label="هامش تقديري"
            value={
              dash.estimated_margin_percent != null
                ? `${dash.estimated_margin_percent.toFixed(1)}%`
                : "—"
            }
          />
        </div>
      )}

      {msg && <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-800">{msg}</div>}

      {/* Purchase package (after approval, assisted mode) */}
      {pkg && pkg.result !== "purchased" && (
        <div className="rounded-lg border-2 border-brand bg-brand/5 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-bold text-brand">حزمة الشراء — نفّذها لدى المورد</h3>
            <button onClick={() => setPkg(null)} className="text-sm text-stone-500">
              إغلاق ✕
            </button>
          </div>
          <ul className="space-y-1 text-sm">
            <li>المورد: {pkg.package.supplier}</li>
            <li>
              رابط المنتج:{" "}
              {pkg.package.product_url ? (
                <a
                  href={pkg.package.product_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand underline"
                >
                  فتح صفحة المورد ↗
                </a>
              ) : (
                "—"
              )}
            </li>
            <li>الكمية: {pkg.package.quantity}</li>
            <li>السعر الأقصى للوحدة: {pkg.package.max_unit_price}</li>
            <li>عنوان الشحن (العميل): {pkg.package.ship_to_address}</li>
          </ul>
          <p className="mt-2 rounded bg-white p-2 text-xs text-stone-600">
            {pkg.package.instructions}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-full border px-3 py-1 text-sm ${
              tab === t ? "border-brand bg-brand text-white" : "border-stone-300"
            }`}
          >
            {STATUS_AR[t]}
            {dash && dash.po_counts[t] ? ` (${dash.po_counts[t]})` : ""}
          </button>
        ))}
      </div>

      {/* PO list */}
      <div className="space-y-3">
        {pos.length === 0 && <p className="text-stone-500">لا توجد أوامر في هذه الحالة.</p>}
        {pos.map((po) => (
          <div key={po.id} className="rounded-lg border border-stone-200 bg-white p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium">
                  {po.product_name} × {po.quantity}
                </p>
                <p className="text-sm text-stone-500">
                  طلب #{po.order_id} · المورد: {po.supplier_name || "—"} · تكلفة متوقعة:{" "}
                  {po.expected_cost ? fmtEGP(po.expected_cost) : "—"}
                </p>
                {po.supplier_order_ref && (
                  <p className="text-xs text-stone-400">مرجع المورد: {po.supplier_order_ref}</p>
                )}
                {po.tracking_no && (
                  <p className="text-xs text-stone-400">تتبع: {po.tracking_no}</p>
                )}
              </div>
              <span className="rounded-full bg-stone-100 px-2 py-1 text-xs">
                {STATUS_AR[po.status]}
              </span>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {po.status === "awaiting_approval" && (
                <>
                  <Btn onClick={() => onApprove(po)}>موافقة</Btn>
                  <Btn variant="ghost" onClick={() => onReject(po)}>
                    رفض
                  </Btn>
                </>
              )}
              {po.status === "purchasing" && (
                <Btn onClick={() => onMarkPurchased(po)}>تسجيل الشراء</Btn>
              )}
              {po.status === "purchased" && <Btn onClick={() => onShip(po)}>تسجيل الشحن</Btn>}
              {po.status === "shipped" && <Btn onClick={() => onDeliver(po)}>تأكيد التسليم</Btn>}
              {po.status === "pending_sourcing" && (
                <span className="text-xs text-amber-700">
                  {po.events[po.events.length - 1]?.note || "بانتظار عرض توريد مناسب"}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Suppliers */}
      <section className="pt-4">
        <h2 className="mb-3 text-lg font-bold">الموردون</h2>
        <div className="grid gap-2 md:grid-cols-2">
          {suppliers.map((s) => (
            <div
              key={s.id}
              className="flex items-center justify-between rounded border border-stone-200 bg-white p-3 text-sm"
            >
              <span>
                {s.name}{" "}
                <span className="text-xs text-stone-400">
                  ({s.kind === "classifieds" ? "إعلانات أفراد" : "متجر"})
                </span>
              </span>
              <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs">
                {s.mode === "api" ? "API آلي" : s.mode === "assisted" ? "مساعَد" : "يدوي"}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4">
      <p className="text-xs text-stone-500">{label}</p>
      <p className="mt-1 text-lg font-bold text-brand">{value}</p>
    </div>
  );
}

function Btn({
  children,
  onClick,
  variant = "solid",
}: {
  children: React.ReactNode;
  onClick: () => void;
  variant?: "solid" | "ghost";
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-4 py-2 text-sm font-semibold ${
        variant === "solid"
          ? "bg-brand text-white hover:bg-brand-dark"
          : "border border-stone-300 text-stone-600 hover:bg-stone-50"
      }`}
    >
      {children}
    </button>
  );
}
