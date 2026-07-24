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

/**
 * Provides cart state and operations to descendant components through React context.
 *
 * @param children - The descendant components that can access the cart context.
 */
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

  const add = async (productId: number, qty = 1) => {
    setCart(await api.addToCart(productId, qty));
    api.track({ event_type: "add_to_cart", product_id: productId });
  };
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

/**
 * Provides access to the cart context.
 *
 * @returns The current cart state and cart operations.
 * @throws An error if used outside `CartProvider`.
 */
export function useCart(): CartCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
