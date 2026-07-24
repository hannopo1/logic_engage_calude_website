"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";
import type { Product } from "@/lib/types";

interface WishlistCtx {
  ids: Set<number>;
  items: Product[];
  count: number;
  loaded: boolean;
  refresh: () => Promise<void>;
  has: (productId: number) => boolean;
  toggle: (productId: number) => Promise<boolean>; // returns new saved-state
}

const Ctx = createContext<WishlistCtx | null>(null);

function loggedIn(): boolean {
  return typeof window !== "undefined" && !!localStorage.getItem("token");
}

/** Tracks the current user's wishlist (product ids + full products) app-wide. */
export function WishlistProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Product[]>([]);
  const [ids, setIds] = useState<Set<number>>(new Set());
  const [loaded, setLoaded] = useState(false);

  const refresh = async () => {
    if (!loggedIn()) {
      setItems([]);
      setIds(new Set());
      setLoaded(true);
      return;
    }
    try {
      const list = await api.wishlist();
      setItems(list);
      setIds(new Set(list.map((p) => p.id)));
    } catch {
      setItems([]);
      setIds(new Set());
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const has = (productId: number) => ids.has(productId);

  const toggle = async (productId: number): Promise<boolean> => {
    const saved = ids.has(productId);
    if (saved) {
      await api.removeWishlist(productId);
    } else {
      await api.addWishlist(productId);
    }
    await refresh();
    return !saved;
  };

  return (
    <Ctx.Provider value={{ ids, items, count: ids.size, loaded, refresh, has, toggle }}>
      {children}
    </Ctx.Provider>
  );
}

export function useWishlist(): WishlistCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useWishlist must be used within WishlistProvider");
  return ctx;
}
