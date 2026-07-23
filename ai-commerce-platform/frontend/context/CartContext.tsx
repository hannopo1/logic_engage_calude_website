"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";
import type { Cart } from "@/lib/types";

interface CartCtx {
  cart: Cart | null;
  refresh: () => Promise<void>;
  add: (productId: number, qty?: number) => Promise<void>;
  update: (productId: number, qty: number) => Promise<void>;
  remove: (productId: number) => Promise<void>;
}

const Ctx = createContext<CartCtx | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart | null>(null);

  const refresh = async () => {
    try {
      setCart(await api.getCart());
    } catch {
      setCart(null);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const add = async (productId: number, qty = 1) =>
    setCart(await api.addToCart(productId, qty));
  const update = async (productId: number, qty: number) =>
    setCart(await api.updateCart(productId, qty));
  const remove = async (productId: number) =>
    setCart(await api.removeFromCart(productId));

  return (
    <Ctx.Provider value={{ cart, refresh, add, update, remove }}>
      {children}
    </Ctx.Provider>
  );
}

export function useCart(): CartCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
