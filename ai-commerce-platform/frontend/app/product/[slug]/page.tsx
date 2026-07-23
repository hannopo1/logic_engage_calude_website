"use client";

import { useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import { useCart } from "@/context/CartContext";
import { api } from "@/lib/api";
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

  if (notFound) return <p className="text-stone-500">Product not found.</p>;
  if (!product) return <p className="text-stone-500">Loading…</p>;

  const onAdd = async () => {
    setBusy(true);
    try {
      await add(product.id, 1);
      alert("Added to cart");
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
          <p className="text-2xl font-bold text-brand">${product.price}</p>
          <p className="text-stone-600">{product.description}</p>
          <p className="text-sm text-stone-500">
            {product.stock_qty > 0
              ? `${product.stock_qty} in stock`
              : "Out of stock"}
          </p>
          <button
            onClick={onAdd}
            disabled={busy || product.stock_qty <= 0}
            className="rounded-md bg-brand px-6 py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {busy ? "Adding…" : "Add to cart"}
          </button>
        </div>
      </div>

      {similar.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">Similar products</h2>
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
            {similar.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {alsoBought.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">Customers also bought</h2>
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
