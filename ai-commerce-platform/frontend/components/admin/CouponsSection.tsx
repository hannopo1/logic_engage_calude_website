"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtEGP } from "@/lib/format";
import type { Coupon } from "@/lib/types";

import { Btn, Field, inputCls } from "./ui";

const EMPTY = {
  code: "",
  kind: "percent",
  value: "",
  min_order: "",
  max_uses: "",
  expires_at: "",
};

/**
 * Provides an administrative interface for creating, viewing, and activating or deactivating discount coupons.
 */
export default function CouponsSection() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [form, setForm] = useState({ ...EMPTY });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () => api.adminCoupons().then(setCoupons).catch(() => {});
  useEffect(() => {
    load();
  }, []);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const create = async () => {
    setErr("");
    if (!form.code.trim() || !form.value) {
      setErr("الكود والقيمة مطلوبان.");
      return;
    }
    setBusy(true);
    try {
      await api.adminCreateCoupon({
        code: form.code.trim(),
        kind: form.kind,
        value: Number(form.value),
        min_order: form.min_order ? Number(form.min_order) : 0,
        max_uses: form.max_uses ? Number(form.max_uses) : null,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : null,
      });
      setForm({ ...EMPTY });
      await load();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const toggle = async (c: Coupon) => {
    await api.adminPatchCoupon(c.id, { is_active: !c.is_active }).catch(() => {});
    await load();
  };

  const kindAr = (k: string) => (k === "fixed" ? "مبلغ ثابت" : "نسبة %");
  const valueAr = (c: Coupon) =>
    c.kind === "fixed" ? fmtEGP(c.value) : `${Number(c.value)}%`;

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-stone-200 bg-white p-4">
        <h2 className="mb-3 text-lg font-bold">إنشاء كود خصم</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="الكود">
            <input
              value={form.code}
              onChange={(e) => set("code", e.target.value.toUpperCase())}
              placeholder="WELCOME10"
              className={inputCls}
            />
          </Field>
          <Field label="النوع">
            <select
              value={form.kind}
              onChange={(e) => set("kind", e.target.value)}
              className={inputCls}
            >
              <option value="percent">نسبة %</option>
              <option value="fixed">مبلغ ثابت (ج.م)</option>
            </select>
          </Field>
          <Field label={form.kind === "fixed" ? "القيمة (ج.م)" : "القيمة (%)"}>
            <input
              type="number"
              value={form.value}
              onChange={(e) => set("value", e.target.value)}
              placeholder={form.kind === "fixed" ? "50" : "10"}
              className={inputCls}
            />
          </Field>
          <Field label="حد أدنى للطلب (ج.م)">
            <input
              type="number"
              value={form.min_order}
              onChange={(e) => set("min_order", e.target.value)}
              placeholder="0"
              className={inputCls}
            />
          </Field>
          <Field label="أقصى عدد استخدامات">
            <input
              type="number"
              value={form.max_uses}
              onChange={(e) => set("max_uses", e.target.value)}
              placeholder="بلا حد"
              className={inputCls}
            />
          </Field>
          <Field label="تاريخ الانتهاء">
            <input
              type="date"
              value={form.expires_at}
              onChange={(e) => set("expires_at", e.target.value)}
              className={inputCls}
            />
          </Field>
        </div>
        {err && <p className="mt-2 text-sm text-red-600">{err}</p>}
        <div className="mt-3">
          <Btn type="button" onClick={create} disabled={busy}>
            {busy ? "جارٍ الحفظ…" : "إنشاء الكود"}
          </Btn>
        </div>
      </div>

      <div className="space-y-2">
        <h2 className="text-lg font-bold">أكواد الخصم ({coupons.length})</h2>
        {coupons.length === 0 && (
          <p className="text-sm text-stone-500">لا توجد أكواد بعد.</p>
        )}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-stone-200 text-right text-stone-500">
                <th className="p-2">الكود</th>
                <th className="p-2">النوع</th>
                <th className="p-2">القيمة</th>
                <th className="p-2">حد أدنى</th>
                <th className="p-2">الاستخدام</th>
                <th className="p-2">الانتهاء</th>
                <th className="p-2">الحالة</th>
                <th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {coupons.map((c) => (
                <tr key={c.id} className="border-b border-stone-100">
                  <td className="p-2 font-mono font-medium">{c.code}</td>
                  <td className="p-2">{kindAr(c.kind)}</td>
                  <td className="p-2">{valueAr(c)}</td>
                  <td className="p-2">{Number(c.min_order) > 0 ? fmtEGP(c.min_order) : "—"}</td>
                  <td className="p-2">
                    {c.used_count}
                    {c.max_uses != null ? ` / ${c.max_uses}` : ""}
                  </td>
                  <td className="p-2">
                    {c.expires_at ? new Date(c.expires_at).toLocaleDateString("ar-EG") : "—"}
                  </td>
                  <td className="p-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs ${
                        c.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-stone-100 text-stone-500"
                      }`}
                    >
                      {c.is_active ? "فعّال" : "موقوف"}
                    </span>
                  </td>
                  <td className="p-2">
                    <button
                      onClick={() => toggle(c)}
                      className="text-xs font-medium text-brand hover:underline"
                    >
                      {c.is_active ? "إيقاف" : "تفعيل"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
