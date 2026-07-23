"use client";

import { useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import { useCart } from "@/context/CartContext";
import { api } from "@/lib/api";
import { fmtEGP } from "@/lib/format";
import type { Product } from "@/lib/types";

export default function ProductPage({ params }: { params: { slug: string } }) {
  const { add } = useCart();
  const [product, setProduct] = useState<Product | null>(null);
  const [similar, setSimilar] = useState<Product[]>([]);
  const [alsoBought, setAlsoBought] = useState<Product[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .product(params.slug)
      .then((p) => {
        setProduct(p);
        return api.recommend(p.id);
      })
      .then((r) => {
        setSimilar(r.similar);
        setAlsoBought(r.also_bought);
      })
      .catch(() => setNotFound(true));
  }, [params.slug]);

  if (notFound) return <p className="text-stone-500">المنتج غير موجود.</p>;
  if (!product) return <p className="text-stone-500">جارٍ التحميل…</p>;

  const onAdd = async () => {
    setBusy(true);
    try {
      await add(product.id, 1);
      alert("تمت الإضافة للسلة");
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-12">
      <div className="grid gap-8 md:grid-cols-2">
        <div className="flex h-80 items-center justify-center rounded-xl bg-stone-100 text-8xl">
          ☕
        </div>
        <div className="space-y-4">
          <h1 className="text-3xl font-bold">{product.name}</h1>
          <p className="text-2xl font-bold text-brand">{fmtEGP(product.price)}</p>
          <p className="text-stone-600">{product.description}</p>
          <p className="text-sm text-stone-500">
            {product.stock_qty > 0 ? "متوفر" : "غير متوفر"}
          </p>
          <button
            onClick={onAdd}
            disabled={busy || product.stock_qty <= 0}
            className="rounded-md bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {busy ? "جارٍ الإضافة…" : "أضف للسلة"}
          </button>
        </div>
      </div>

      {similar.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">منتجات مشابهة</h2>
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
            {similar.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {alsoBought.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">اشترى العملاء أيضاً</h2>
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
            {alsoBought.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
