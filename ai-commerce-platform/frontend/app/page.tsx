"use client";

import { ArrowLeft, ShieldCheck, Sparkles, Truck, Wallet } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import SearchBar from "@/components/SearchBar";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

const TRUST = [
  { icon: Truck, label: "توصيل لكل مصر" },
  { icon: Wallet, label: "الدفع عند الاستلام" },
  { icon: ShieldCheck, label: "تقييمات موثّقة" },
];

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
    <div className="space-y-12">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl bg-ink px-6 py-16 text-center text-white sm:py-20">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              "radial-gradient(60% 60% at 50% 0%, rgba(198,138,46,0.35) 0%, rgba(28,25,23,0) 70%)",
          }}
        />
        <div className="relative mx-auto flex max-w-2xl flex-col items-center gap-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-sm text-brand-light">
            <Sparkles className="h-4 w-4" />
            قهوة مختصة + مساعد ذكي
          </span>
          <h1 className="text-4xl font-extrabold leading-tight sm:text-5xl">
            اصنع قهوة <span className="text-brand-light">أفضل</span>.
          </h1>
          <p className="max-w-xl text-white/80">
            بن مختص وأدوات تحضير دقيقة — ومساعد ذكي يرشّح لك بالضبط ما تحتاجه.
            توصيل لكل المحافظات والدفع عند الاستلام.
          </p>
          <SearchBar />
          <Link
            href="/products"
            className="inline-flex items-center gap-2 rounded-full bg-brand px-6 py-3 font-semibold text-ink transition hover:bg-brand-light"
          >
            تصفّح كل المنتجات
            <ArrowLeft className="h-4 w-4" />
          </Link>

          <div className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 text-sm text-white/70">
            {TRUST.map(({ icon: Icon, label }) => (
              <span key={label} className="inline-flex items-center gap-1.5">
                <Icon className="h-4 w-4 text-brand-light" />
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Featured */}
      <section>
        <div className="mb-5 flex items-end justify-between">
          <h2 className="text-2xl font-extrabold text-ink">منتجات مميزة</h2>
          <Link href="/products" className="text-sm font-semibold text-brand hover:text-brand-dark">
            عرض الكل
          </Link>
        </div>
        {loading ? (
          <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-72 animate-pulse rounded-2xl bg-stone-200/60" />
            ))}
          </div>
        ) : featured.length === 0 ? (
          <p className="text-muted">
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
