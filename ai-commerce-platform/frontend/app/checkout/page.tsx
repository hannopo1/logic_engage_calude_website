"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useCart } from "@/context/CartContext";
import { api } from "@/lib/api";
import type { Order } from "@/lib/types";

export default function CheckoutPage() {
  const { cart, refresh } = useCart();
  const router = useRouter();
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const o = await api.checkout(address);
      setOrder(o);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (order) {
    return (
      <div className="space-y-4 text-center">
        <h1 className="text-2xl font-bold text-green-700">Order confirmed ✓</h1>
        <p>
          Order <strong>#{order.id}</strong> — total{" "}
          <strong>${order.total_amount}</strong>
        </p>
        <p className="text-stone-500">Status: {order.status}</p>
        <button
          onClick={() => router.push("/products")}
          className="rounded-md bg-brand px-6 py-3 font-semibold text-white"
        >
          Continue shopping
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md space-y-6">
      <h1 className="text-2xl font-bold">Checkout</h1>
      {cart && (
        <p className="text-stone-600">
          {cart.item_count} item(s) — subtotal{" "}
          <span className="font-bold text-brand">${cart.subtotal}</span>
        </p>
      )}
      <form onSubmit={submit} className="space-y-4">
        <textarea
          required
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Shipping address"
          rows={3}
          className="w-full rounded-md border border-stone-300 p-3 outline-none focus:border-brand"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy || !cart || cart.items.length === 0}
          className="w-full rounded-md bg-brand py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {busy ? "Placing order…" : "Place order"}
        </button>
      </form>
      <p className="text-center text-xs text-stone-400">
        Payment is simulated in this MVP (cash-on-delivery). Real payment
        integration is on the roadmap.
      </p>
    </div>
  );
}
