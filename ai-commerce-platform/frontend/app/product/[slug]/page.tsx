"use client";

import { Check, Coffee, ShoppingCart, Truck } from "lucide-react";
import { useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import ProductReviews from "@/components/ProductReviews";
import { Stars } from "@/components/Stars";
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
  const [added, setAdded] = useState(false);

  useEffect(() => {
    api
      .product(params.slug)
      .then((p) => {
        setProduct(p);
        api.track({ event_type: "product_view", product_id: p.id });
        return api.recommend(p.id);
      })
      .then((r) => {
        setSimilar(r.similar);
        setAlsoBought(r.also_bought);
      })
      .catch(() => setNotFound(true));
  }, [params.slug]);

  if (notFound) return <p className="text-muted">المنتج غير موجود.</p>;
  if (!product) return <p className="text-muted">جارٍ التحميل…</p>;

  const soldOut = product.stock_qty <= 0;
  const count = product.rating_count ?? 0;

  const onAdd = async () => {
    setBusy(true);
    try {
      await add(product.id, 1);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch (e) {
      alert((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-14">
      <div className="grid gap-8 md:grid-cols-2">
        {/* Gallery */}
        <div className="aspect-square overflow-hidden rounded-3xl border border-line bg-gradient-to-br from-stone-100 to-stone-200">
          {product.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={product.image} alt={product.name} className="h-full w-full object-cover" />
          ) : (
            <div className="grid h-full w-full place-items-center text-stone-300">
              <Coffee className="h-24 w-24" />
            </div>
          )}
        </div>

        {/* Buy box (sticky on desktop) */}
        <div className="space-y-5 md:sticky md:top-24 md:self-start">
          <h1 className="text-3xl font-extrabold leading-tight text-ink">{product.name}</h1>

          <div className="flex items-center gap-2 text-sm text-muted">
            {count > 0 ? (
              <>
                <Stars value={product.rating_avg ?? 0} size={16} />
                <span>{(product.rating_avg ?? 0).toFixed(1)} · {count} تقييم</span>
              </>
            ) : (
              <span className="text-stone-400">لا توجد تقييمات بعد</span>
            )}
          </div>

          <p className="text-3xl font-extrabold text-brand">{fmtEGP(product.price)}</p>
          <p className="leading-7 text-ink/80">{product.description}</p>

          <div className="flex items-center gap-2 text-sm">
            {soldOut ? (
              <span className="rounded-full bg-stone-100 px-3 py-1 font-medium text-muted">غير متوفر حالياً</span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-3 py-1 font-medium text-green-700">
                <Check className="h-4 w-4" /> متوفر — جاهز للشحن
              </span>
            )}
          </div>

          <button
            onClick={onAdd}
            disabled={busy || soldOut}
            className="flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-dark py-3.5 font-semibold text-white transition hover:bg-ink disabled:opacity-50"
          >
            {added ? <Check className="h-5 w-5" /> : <ShoppingCart className="h-5 w-5" />}
            {soldOut ? "غير متوفر" : busy ? "جارٍ الإضافة…" : added ? "تمت الإضافة ✓" : "أضف للسلة"}
          </button>

          <div className="flex items-center gap-2 rounded-2xl border border-line bg-white p-3 text-sm text-muted">
            <Truck className="h-5 w-5 text-brand" />
            توصيل لكل المحافظات · الدفع عند الاستلام
          </div>
        </div>
      </div>

      {/* Reviews */}
      <ProductReviews productId={product.id} slug={product.slug} />

      {similar.length > 0 && (
        <section>
          <h2 className="mb-5 text-xl font-extrabold text-ink">منتجات مشابهة</h2>
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
            {similar.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {alsoBought.length > 0 && (
        <section>
          <h2 className="mb-5 text-xl font-extrabold text-ink">اشترى العملاء أيضاً</h2>
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
