"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import SearchBar from "@/components/SearchBar";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .products("?page=1&page_size=8")
      .then((r) => setFeatured(r.items))
      .catch(() => setFeatured([]))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-10">
      <section className="flex flex-col items-center gap-6 rounded-2xl bg-gradient-to-br from-brand to-brand-dark px-6 py-16 text-center text-white">
        <h1 className="text-4xl font-bold">اصنع قهوة أفضل.</h1>
        <p className="max-w-xl text-white/90">
          بن مختص وأدوات دقيقة — مع مساعد ذكي يساعدك تختار بالضبط اللي محتاجه.
          توصيل لكل مصر والدفع عند الاستلام.
        </p>
        <SearchBar />
        <Link
          href="/products"
          className="rounded-full bg-white px-6 py-3 font-semibold text-brand hover:bg-stone-100"
        >
          تصفّح كل المنتجات
        </Link>
      </section>

      <section>
        <h2 className="mb-4 text-2xl font-bold">منتجات مميزة</h2>
        {loading ? (
          <p className="text-stone-500">جارٍ التحميل…</p>
        ) : featured.length === 0 ? (
          <p className="text-stone-500">
            لا توجد منتجات بعد. شغّل <code>make seed</code> لتحميل الكتالوج التجريبي.
          </p>
        ) : (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
            {featured.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
