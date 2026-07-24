"use client";

import { Coffee, LayoutGrid, ShoppingBag, ShoppingCart, User } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCart } from "@/context/CartContext";

const LINKS = [
  { href: "/products", label: "المتجر", icon: LayoutGrid },
  { href: "/orders", label: "طلباتي", icon: ShoppingBag },
  { href: "/login", label: "حسابي", icon: User },
];

/**
 * Renders the application navigation bar with route links and the current cart item count.
 */
export default function Navbar() {
  const { cart } = useCart();
  const count = cart?.item_count ?? 0;
  const pathname = usePathname();

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/80 backdrop-blur-md">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 text-lg font-extrabold text-ink">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-ink text-brand-light">
            <Coffee className="h-5 w-5" />
          </span>
          كيڤ برو
        </Link>

        <div className="flex items-center gap-1 text-sm sm:gap-2">
          {LINKS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-1.5 rounded-full px-3 py-2 font-medium transition ${
                isActive(href)
                  ? "bg-ink text-white"
                  : "text-muted hover:bg-ink/5 hover:text-ink"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{label}</span>
            </Link>
          ))}

          <Link
            href="/admin"
            className={`hidden rounded-full px-3 py-2 font-medium transition sm:block ${
              isActive("/admin") ? "bg-ink text-white" : "text-muted/70 hover:text-ink"
            }`}
          >
            الإدارة
          </Link>

          <Link
            href="/cart"
            aria-label="السلة"
            className="relative flex items-center gap-1.5 rounded-full bg-brand-dark px-3 py-2 font-semibold text-white hover:bg-ink"
          >
            <ShoppingCart className="h-4 w-4" />
            <span className="hidden sm:inline">السلة</span>
            {count > 0 && (
              <span className="absolute -left-1.5 -top-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-brand px-1 text-xs font-bold text-ink ring-2 ring-paper">
                {count}
              </span>
            )}
          </Link>
        </div>
      </nav>
    </header>
  );
}
