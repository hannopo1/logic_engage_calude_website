"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, setToken } from "@/lib/api";
import { useCart } from "@/context/CartContext";

export default function LoginPage() {
  const router = useRouter();
  const { refresh } = useCart();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const res =
        mode === "login"
          ? await api.login({ email, password })
          : await api.register({ email, password });
      setToken(res.access_token);
      await refresh();
      router.push("/products");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-sm space-y-6">
      <h1 className="text-2xl font-bold">
        {mode === "login" ? "تسجيل الدخول" : "إنشاء حساب"}
      </h1>
      <form onSubmit={submit} className="space-y-4">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="البريد الإلكتروني"
          className="w-full rounded-md border border-stone-300 p-3 outline-none focus:border-brand"
        />
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="كلمة المرور"
          className="w-full rounded-md border border-stone-300 p-3 outline-none focus:border-brand"
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded-md bg-brand py-3 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {busy ? "…" : mode === "login" ? "دخول" : "تسجيل"}
        </button>
      </form>
      <button
        onClick={() => setMode(mode === "login" ? "register" : "login")}
        className="text-sm text-brand underline"
      >
        {mode === "login"
          ? "ليس لديك حساب؟ سجّل الآن"
          : "لديك حساب؟ سجّل الدخول"}
      </button>
      <p className="text-xs text-stone-400">
        حساب تجريبي: demo@example.com / demo1234 — للإدارة: admin@example.com / admin1234
      </p>
    </div>
  );
}
