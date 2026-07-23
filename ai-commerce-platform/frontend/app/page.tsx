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
        <h1 className="text-4xl font-bold">Brew better coffee.</h1>
        <p className="max-w-xl text-white/90">
          Specialty beans and precision gear — with an AI assistant that helps you
          pick exactly what you need.
        </p>
        <SearchBar />
        <Link
          href="/products"
          className="rounded-full bg-white px-6 py-3 font-semibold text-brand hover:bg-stone-100"
        >
          Shop all products
        </Link>
      </section>

      <section>
        <h2 className="mb-4 text-2xl font-bold">Featured</h2>
        {loading ? (
          <p className="text-stone-500">Loading…</p>
        ) : featured.length === 0 ? (
          <p className="text-stone-500">
            No products yet. Run <code>make seed</code> to load the demo catalog.
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
