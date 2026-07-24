"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api } from "@/lib/api";

/**
 * Renders a search form that tracks valid queries and navigates to the products results page.
 *
 * Whitespace-only queries are ignored.
 */
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
    <form onSubmit={submit} className="relative w-full max-w-xl">
      <Search className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" />
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="ابحث مثلاً: 'مطحنة قهوة للإسبريسو'…"
        className="w-full rounded-full border border-line bg-white px-5 py-3 pr-11 text-ink outline-none focus:border-brand focus:ring-2 focus:ring-brand/25"
      />
    </form>
  );
}
