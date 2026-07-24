"use client";

import { BadgeCheck } from "lucide-react";
import { useEffect, useState } from "react";

import { Stars, StarInput } from "@/components/Stars";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { ReviewBlock } from "@/lib/types";

function loggedIn(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("token");
}

export default function ProductReviews({
  productId,
  slug,
}: {
  productId: number;
  slug: string;
}) {
  const [data, setData] = useState<ReviewBlock | null>(null);
  const [rating, setRating] = useState(0);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [authed, setAuthed] = useState(false);

  const load = () => api.productReviews(slug).then(setData).catch(() => setData(null));
  useEffect(() => {
    setAuthed(loggedIn());
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [slug]);

  const submit = async () => {
    setErr("");
    setMsg("");
    if (rating < 1) {
      setErr("اختر عدد النجوم أولاً.");
      return;
    }
    if (!body.trim()) {
      setErr("اكتب رأيك في المنتج.");
      return;
    }
    setBusy(true);
    try {
      await api.submitReview(productId, { rating, title: title.trim() || undefined, body: body.trim() });
      setMsg("شكراً لك! ستظهر مراجعتك بعد اعتماد الإدارة.");
      setRating(0);
      setTitle("");
      setBody("");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const summary = data?.summary;
  const total = summary?.count ?? 0;

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-extrabold text-ink">تقييمات العملاء</h2>

      {/* Summary */}
      <div className="grid gap-6 rounded-2xl border border-line bg-white p-5 sm:grid-cols-[auto_1fr] sm:items-center">
        <div className="text-center sm:pl-6 sm:border-l sm:border-line">
          <div className="text-4xl font-extrabold text-ink">{(summary?.average ?? 0).toFixed(1)}</div>
          <div className="mt-1 flex justify-center">
            <Stars value={summary?.average ?? 0} size={18} />
          </div>
          <div className="mt-1 text-xs text-muted">{total} تقييم</div>
        </div>
        <div className="space-y-1.5">
          {[5, 4, 3, 2, 1].map((star) => {
            const c = summary?.distribution?.[String(star)] ?? 0;
            const pct = total ? Math.round((c / total) * 100) : 0;
            return (
              <div key={star} className="flex items-center gap-2 text-xs text-muted">
                <span className="w-6 shrink-0">{star} ★</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-stone-100">
                  <div className="h-full rounded-full bg-brand" style={{ width: `${pct}%` }} />
                </div>
                <span className="w-8 shrink-0 text-left">{c}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Write a review */}
      <div className="rounded-2xl border border-line bg-white p-5">
        <h3 className="mb-3 font-bold text-ink">اكتب مراجعتك</h3>
        {authed ? (
          <div className="space-y-3">
            <StarInput value={rating} onChange={setRating} />
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="عنوان مختصر (اختياري)"
              className="w-full rounded-xl border border-line p-3 text-sm outline-none focus:border-brand"
            />
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="شاركنا تجربتك مع المنتج…"
              rows={3}
              className="w-full rounded-xl border border-line p-3 text-sm outline-none focus:border-brand"
            />
            {err && <p className="text-sm text-red-600">{err}</p>}
            {msg && <p className="text-sm text-green-700">{msg}</p>}
            <button
              onClick={submit}
              disabled={busy}
              className="rounded-xl bg-brand-dark px-5 py-2.5 text-sm font-semibold text-white hover:bg-ink disabled:opacity-50"
            >
              {busy ? "جارٍ الإرسال…" : "إرسال المراجعة"}
            </button>
            <p className="text-xs text-muted">يمكن تقييم المنتج فقط بعد شرائه من المتجر.</p>
          </div>
        ) : (
          <p className="text-sm text-muted">
            <a href="/login" className="font-semibold text-brand hover:underline">
              سجّل الدخول
            </a>{" "}
            لتتمكن من تقييم المنتجات التي اشتريتها.
          </p>
        )}
      </div>

      {/* List */}
      <div className="space-y-3">
        {total === 0 ? (
          <p className="text-sm text-muted">كن أول من يقيّم هذا المنتج.</p>
        ) : (
          data?.items.map((r) => (
            <div key={r.id} className="rounded-2xl border border-line bg-white p-4">
              <div className="flex items-center justify-between">
                <Stars value={r.rating} size={15} />
                {r.is_verified && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700">
                    <BadgeCheck className="h-3.5 w-3.5" /> شراء موثّق
                  </span>
                )}
              </div>
              {r.title && <p className="mt-2 font-bold text-ink">{r.title}</p>}
              <p className="mt-1 text-sm leading-6 text-ink/80">{r.body}</p>
              <p className="mt-2 text-xs text-muted">{fmtDate(r.created_at)}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
