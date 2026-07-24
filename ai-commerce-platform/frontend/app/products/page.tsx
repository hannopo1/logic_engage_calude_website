"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import SearchBar from "@/components/SearchBar";
import { api } from "@/lib/api";
import type { Category, Product } from "@/lib/types";

function ProductsInner() {
  const params = useSearchParams();
  const q = params.get("q") || "";
  const category = params.get("category") || "";

  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    setLoading(true);
    const load = q
      ? api.search(q)
      : api
          .products(category ? `?category=${category}&page_size=24` : "?page_size=24")
          .then((r) => r.items);
    load
      .then(setProducts)
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [q, category]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-4">
        <SearchBar />
      </div>

      <div className="flex flex-wrap gap-2">
        <a
          href="/products"
          className={`rounded-full border px-4 py-1.5 text-sm font-medium transition ${
            !category
              ? "border-ink bg-ink text-white"
              : "border-line text-muted hover:border-ink hover:text-ink"
          }`}
        >
          الكل
        </a>
        {categories.map((c) => (
          <a
            key={c.id}
            href={`/products?category=${c.slug}`}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition ${
              category === c.slug
                ? "border-ink bg-ink text-white"
                : "border-line text-muted hover:border-ink hover:text-ink"
            }`}
          >
            {c.name}
          </a>
        ))}
      </div>

      <h1 className="text-xl font-extrabold text-ink">
        {q ? `نتائج البحث عن «${q}»` : "كل المنتجات"}
      </h1>

      {loading ? (
        <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-72 animate-pulse rounded-2xl bg-stone-200/60" />
          ))}
        </div>
      ) : products.length === 0 ? (
        <p className="text-muted">لا توجد منتجات مطابقة.</p>
      ) : (
        <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<p className="text-stone-500">جارٍ التحميل…</p>}>
      <ProductsInner />
    </Suspense>
  );
}
