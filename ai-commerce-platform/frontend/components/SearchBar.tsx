"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";

export default function SearchBar() {
  const router = useRouter();
  const [q, setQ] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const term = q.trim();
    if (!term) return;
    api.track({ event_type: "search", query: term });
    router.push(`/products?q=${encodeURIComponent(term)}`);
  };

  return (
    <form onSubmit={submit} className="w-full max-w-xl">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="ابحث مثلاً: 'مطحنة قهوة للإسبريسو'…"
        className="w-full rounded-full border border-stone-300 px-5 py-3 outline-none focus:border-brand focus:ring-2 focus:ring-brand/30"
      />
    </form>
  );
}
