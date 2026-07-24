"use client";

import { Fragment, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtEGP } from "@/lib/format";
import type { Offer, ProductAdmin, Supplier } from "@/lib/types";
import { Btn, Field, inputCls } from "./ui";

/**
 * Displays the admin product list and provides controls for adding products and managing dropshipping offers.
 */
export default function ProductsSection() {
  const [products, setProducts] = useState<ProductAdmin[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [msg, setMsg] = useState("");

  const load = async () => setProducts(await api.adminProducts());
  useEffect(() => {
    load();
    api.adminSuppliers().then(setSuppliers).catch(() => {});
  }, []);

  const flash = (t: string) => {
    setMsg(t);
    setTimeout(() => setMsg(""), 4000);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">المنتجات ({products.length})</h2>
        <Btn onClick={() => setShowForm((s) => !s)}>{showForm ? "إغلاق" : "+ إضافة منتج"}</Btn>
      </div>
      {msg && <div className="rounded-md bg-green-50 p-3 text-sm text-green-800">{msg}</div>}

      {showForm && (
        <AddProductForm
          onCreated={async () => {
            await load();
            flash("تمت إضافة المنتج. للمنتجات الموردة: افتح «العروض» واربط رابط أمازون/نون.");
            setShowForm(false);
          }}
        />
      )}

      <div className="overflow-x-auto rounded-lg border border-stone-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-stone-50 text-stone-500">
            <tr>
              <th className="p-3 text-right">المنتج</th>
              <th className="p-3 text-center">السعر</th>
              <th className="p-3 text-center">النوع</th>
              <th className="p-3 text-center">المخزون</th>
              <th className="p-3 text-center">العروض</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {products.map((p) => (
              <Fragment key={p.id}>
                <tr className="hover:bg-stone-50">
                  <td className="p-3">{p.name}</td>
                  <td className="p-3 text-center font-medium text-brand">{fmtEGP(p.price)}</td>
                  <td className="p-3 text-center">
                    <span className="rounded-full bg-stone-100 px-2 py-0.5 text-xs">
                      {p.fulfillment_type === "own_stock" ? "مخزون خاص" : "دروب شيبينج"}
                    </span>
                  </td>
                  <td className="p-3 text-center">{p.fulfillment_type === "own_stock" ? p.stock_qty : "—"}</td>
                  <td className="p-3 text-center">
                    {p.fulfillment_type === "dropship" ? (
                      <button
                        onClick={() => setExpanded(expanded === p.id ? null : p.id)}
                        className="text-brand underline"
                      >
                        عروض ({p.offer_count})
                      </button>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
                {expanded === p.id && (
                  <tr>
                    <td colSpan={5} className="bg-stone-50 p-4">
                      <OffersEditor productId={p.id} suppliers={suppliers} onChange={load} />
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Renders a form for creating a product.
 *
 * @param onCreated - Callback invoked after the product is created successfully.
 */
function AddProductForm({ onCreated }: { onCreated: () => void }) {
  const [f, setF] = useState({
    name: "",
    price: "",
    description: "",
    tags: "",
    fulfillment_type: "dropship",
    stock_qty: "0",
    cost_price: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const set = (k: string, v: string) => setF((p) => ({ ...p, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr("");
    try {
      await api.adminCreateProduct({
        name: f.name,
        price: f.price,
        description: f.description || null,
        tags: f.tags || null,
        fulfillment_type: f.fulfillment_type,
        stock_qty: f.fulfillment_type === "own_stock" ? Number(f.stock_qty || 0) : 100,
        cost_price: f.fulfillment_type === "own_stock" && f.cost_price ? f.cost_price : null,
      });
      onCreated();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="grid gap-3 rounded-lg border border-stone-200 bg-white p-4 md:grid-cols-2">
      <Field label="اسم المنتج">
        <input className={inputCls} value={f.name} onChange={(e) => set("name", e.target.value)} required />
      </Field>
      <Field label="سعر البيع (ج.م)">
        <input className={inputCls} type="number" step="0.01" value={f.price} onChange={(e) => set("price", e.target.value)} required />
      </Field>
      <Field label="الوصف">
        <input className={inputCls} value={f.description} onChange={(e) => set("description", e.target.value)} />
      </Field>
      <Field label="الوسوم (مفصولة بفاصلة)">
        <input className={inputCls} value={f.tags} onChange={(e) => set("tags", e.target.value)} placeholder="قهوة,coffee" />
      </Field>
      <Field label="نوع التوريد">
        <select className={inputCls} value={f.fulfillment_type} onChange={(e) => set("fulfillment_type", e.target.value)}>
          <option value="dropship">دروب شيبينج (شراء من مورد عند البيع)</option>
          <option value="own_stock">مخزون خاص (بيع من عندك)</option>
        </select>
      </Field>
      {f.fulfillment_type === "own_stock" ? (
        <div className="grid grid-cols-2 gap-3">
          <Field label="الكمية بالمخزون">
            <input className={inputCls} type="number" value={f.stock_qty} onChange={(e) => set("stock_qty", e.target.value)} />
          </Field>
          <Field label="تكلفتك (ج.م)">
            <input className={inputCls} type="number" step="0.01" value={f.cost_price} onChange={(e) => set("cost_price", e.target.value)} />
          </Field>
        </div>
      ) : (
        <div className="flex items-end text-xs text-stone-500">
          بعد الحفظ، افتح «العروض» واربط رابط أمازون/نون وتكلفتهما.
        </div>
      )}
      {err && <p className="text-sm text-red-600 md:col-span-2">{err}</p>}
      <div className="md:col-span-2">
        <Btn type="submit" disabled={busy}>
          {busy ? "جارٍ الحفظ…" : "حفظ المنتج"}
        </Btn>
      </div>
    </form>
  );
}

/**
 * Displays and manages supplier offers for a product.
 *
 * @param productId - The product whose supplier offers are managed
 * @param suppliers - Suppliers available for offer selection
 * @param onChange - Callback invoked after an offer is added
 */
function OffersEditor({
  productId,
  suppliers,
  onChange,
}: {
  productId: number;
  suppliers: Supplier[];
  onChange: () => void;
}) {
  const [offers, setOffers] = useState<Offer[]>([]);
  const marketplaces = suppliers.filter((s) => s.kind !== "classifieds");
  const [supplierId, setSupplierId] = useState<number | "">("");
  const [url, setUrl] = useState("");
  const [price, setPrice] = useState("");
  const [ship, setShip] = useState("0");
  const [busy, setBusy] = useState(false);

  const load = async () => setOffers(await api.adminOffersFor(productId));
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [productId]);

  const supName = (id: number) => suppliers.find((s) => s.id === id)?.name || `#${id}`;

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId) return;
    setBusy(true);
    try {
      await api.adminCreateOffer({
        product_id: productId,
        supplier_id: supplierId,
        url,
        supplier_price: price,
        shipping_cost: ship || "0",
      });
      setUrl("");
      setPrice("");
      setShip("0");
      await load();
      onChange();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">عروض التوريد (يختار الوكيل الأرخص تلقائياً)</p>
      {offers.length === 0 ? (
        <p className="text-xs text-stone-500">لا عروض بعد — أضف رابط أمازون/نون وتكلفته.</p>
      ) : (
        <ul className="space-y-1 text-sm">
          {offers.map((o) => (
            <li key={o.id} className="flex items-center gap-3">
              <span className="rounded bg-white px-2 py-0.5 text-xs">{supName(o.supplier_id)}</span>
              <span>التكلفة: {fmtEGP(o.supplier_price)} + شحن {fmtEGP(o.shipping_cost)}</span>
              {o.url && (
                <a href={o.url} target="_blank" rel="noreferrer" className="text-brand underline">
                  الرابط ↗
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={add} className="flex flex-wrap items-end gap-2">
        <Field label="المورد">
          <select className={inputCls} value={supplierId} onChange={(e) => setSupplierId(Number(e.target.value))} required>
            <option value="">اختر…</option>
            {marketplaces.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="رابط المنتج لدى المورد">
          <input className={inputCls} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://www.amazon.eg/dp/…" />
        </Field>
        <Field label="تكلفة المورد">
          <input className={inputCls} type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} required />
        </Field>
        <Field label="الشحن">
          <input className={inputCls} type="number" step="0.01" value={ship} onChange={(e) => setShip(e.target.value)} />
        </Field>
        <Btn type="submit" disabled={busy}>
          {busy ? "…" : "إضافة عرض"}
        </Btn>
      </form>
    </div>
  );
}
