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
          className={`rounded-full border px-3 py-1 text-sm ${
            !category ? "border-brand bg-brand text-white" : "border-stone-300"
          }`}
        >
          الكل
        </a>
        {categories.map((c) => (
          <a
            key={c.id}
            href={`/products?category=${c.slug}`}
            className={`rounded-full border px-3 py-1 text-sm ${
              category === c.slug
                ? "border-brand bg-brand text-white"
                : "border-stone-300"
            }`}
          >
            {c.name}
          </a>
        ))}
      </div>

      <h1 className="text-xl font-semibold">
        {q ? `نتائج البحث عن «${q}»` : "كل المنتجات"}
      </h1>

      {loading ? (
        <p className="text-stone-500">جارٍ التحميل…</p>
      ) : products.length === 0 ? (
        <p className="text-stone-500">لا توجد منتجات مطابقة.</p>
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
