"use client";

import { Check, Star, X } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { AdminReview } from "@/lib/types";

/**
 * Displays product reviews with filtering, approval, and deletion controls.
 */
export default function ReviewsSection() {
  const [reviews, setReviews] = useState<AdminReview[]>([]);
  const [status, setStatus] = useState<"pending" | "all">("pending");

  const load = (s: "pending" | "all") => api.adminReviews(s).then(setReviews).catch(() => {});
  useEffect(() => {
    load(status);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const approve = async (id: number) => {
    await api.adminApproveReview(id).catch(() => {});
    load(status);
  };
  const reject = async (id: number) => {
    await api.adminRejectReview(id).catch(() => {});
    load(status);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-ink">إشراف التقييمات</h2>
        <div className="flex gap-1 rounded-full bg-stone-100 p-1 text-sm">
          {(["pending", "all"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`rounded-full px-3 py-1 font-medium ${
                status === s ? "bg-ink text-white" : "text-muted"
              }`}
            >
              {s === "pending" ? "بانتظار الاعتماد" : "الكل"}
            </button>
          ))}
        </div>
      </div>

      {reviews.length === 0 && (
        <p className="text-sm text-muted">
          {status === "pending" ? "لا توجد تقييمات بانتظار الاعتماد." : "لا توجد تقييمات."}
        </p>
      )}

      <div className="space-y-3">
        {reviews.map((r) => (
          <div key={r.id} className="rounded-2xl border border-line bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-0.5 text-brand">
                    {Array.from({ length: r.rating }).map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-brand" />
                    ))}
                  </span>
                  <span className="text-xs text-muted">منتج #{r.product_id}</span>
                  {r.is_approved ? (
                    <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
                      معتمد
                    </span>
                  ) : (
                    <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
                      بانتظار
                    </span>
                  )}
                </div>
                {r.title && <p className="mt-1 font-bold text-ink">{r.title}</p>}
                <p className="mt-1 text-sm text-ink/80">{r.body}</p>
                <p className="mt-1 text-xs text-muted">{fmtDate(r.created_at)}</p>
              </div>
              <div className="flex shrink-0 gap-2">
                {!r.is_approved && (
                  <button
                    onClick={() => approve(r.id)}
                    className="inline-flex items-center gap-1 rounded-lg bg-green-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-green-700"
                  >
                    <Check className="h-4 w-4" /> اعتماد
                  </button>
                )}
                <button
                  onClick={() => reject(r.id)}
                  className="inline-flex items-center gap-1 rounded-lg border border-line px-3 py-1.5 text-sm font-semibold text-red-600 hover:bg-red-50"
                >
                  <X className="h-4 w-4" /> حذف
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
