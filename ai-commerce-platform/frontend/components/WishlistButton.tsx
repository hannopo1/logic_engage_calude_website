"use client";

import { Heart } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useWishlist } from "@/context/WishlistContext";

function loggedIn(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("token");
}

/**
 * Heart toggle to save/remove a product from the wishlist.
 * `variant="icon"` renders a circular overlay button (product cards);
 * `variant="button"` renders a full labelled button (product page).
 */
export default function WishlistButton({
  productId,
  variant = "icon",
}: {
  productId: number;
  variant?: "icon" | "button";
}) {
  const { has, toggle } = useWishlist();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const saved = has(productId);

  const onClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!loggedIn()) {
      router.push("/login");
      return;
    }
    setBusy(true);
    try {
      await toggle(productId);
    } catch {
      /* ignore */
    } finally {
      setBusy(false);
    }
  };

  if (variant === "button") {
    return (
      <button
        onClick={onClick}
        disabled={busy}
        aria-pressed={saved}
        className={`flex w-full items-center justify-center gap-2 rounded-2xl border py-3 font-semibold transition disabled:opacity-50 ${
          saved
            ? "border-brand bg-brand/10 text-brand-dark"
            : "border-line text-ink hover:bg-stone-50"
        }`}
      >
        <Heart className={`h-5 w-5 ${saved ? "fill-brand text-brand" : ""}`} />
        {saved ? "في المفضلة" : "أضف للمفضلة"}
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      disabled={busy}
      aria-label={saved ? "إزالة من المفضلة" : "أضف للمفضلة"}
      aria-pressed={saved}
      className="absolute left-2 top-2 grid h-9 w-9 place-items-center rounded-full bg-white/90 text-ink shadow-card backdrop-blur transition hover:bg-white disabled:opacity-50"
    >
      <Heart className={`h-4 w-4 ${saved ? "fill-red-500 text-red-500" : "text-ink"}`} />
    </button>
  );
}
