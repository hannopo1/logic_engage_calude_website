"use client";

import { Heart } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import ProductCard from "@/components/ProductCard";
import { useWishlist } from "@/context/WishlistContext";

function loggedIn(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("token");
}

export default function WishlistPage() {
  const { items, loaded, refresh } = useWishlist();
  const [authed, setAuthed] = useState<boolean | null>(null);

  useEffect(() => {
    setAuthed(loggedIn());
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (authed === false) {
    return (
      <div className="mx-auto max-w-md space-y-4 rounded-2xl border border-line bg-white p-10 text-center">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-stone-100 text-muted">
          <Heart className="h-8 w-8" />
        </div>
        <h1 className="text-2xl font-extrabold text-ink">قائمة المفضلة</h1>
        <p className="text-muted">سجّل الدخول لحفظ منتجاتك المفضلة والوصول إليها من أي جهاز.</p>
        <Link
          href="/login"
          className="inline-block rounded-xl bg-brand-dark px-5 py-2.5 font-semibold text-white hover:bg-ink"
        >
          تسجيل الدخول
        </Link>
      </div>
    );
  }

  if (authed === null || !loaded) return <p className="text-muted">جارٍ التحميل…</p>;

  return (
    <div className="space-y-6">
      <h1 className="flex items-center gap-2 text-2xl font-extrabold text-ink">
        <Heart className="h-6 w-6 fill-red-500 text-red-500" />
        قائمة المفضلة
      </h1>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-line bg-white p-10 text-center">
          <p className="text-muted">لا توجد منتجات في مفضلتك بعد.</p>
          <Link href="/products" className="mt-3 inline-block font-semibold text-brand hover:underline">
            تصفّح المنتجات
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-5 md:grid-cols-4">
          {items.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}
    </div>
  );
}
