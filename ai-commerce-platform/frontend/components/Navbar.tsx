"use client";

import Link from "next/link";

import { useCart } from "@/context/CartContext";

export default function Navbar() {
  const { cart } = useCart();
  const count = cart?.item_count ?? 0;

  return (
    <header className="sticky top-0 z-40 border-b border-stone-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold text-brand">
          ☕ CaveBrew
        </Link>
        <div className="flex items-center gap-5 text-sm">
          <Link href="/products" className="hover:text-brand">
            Shop
          </Link>
          <Link href="/login" className="hover:text-brand">
            Account
          </Link>
          <Link href="/cart" className="relative hover:text-brand">
            Cart
            {count > 0 && (
              <span className="absolute -right-4 -top-2 rounded-full bg-brand px-1.5 text-xs font-bold text-white">
                {count}
              </span>
            )}
          </Link>
        </div>
      </nav>
    </header>
  );
}
