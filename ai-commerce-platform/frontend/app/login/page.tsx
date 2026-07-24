"use client";

import { Coffee } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, setToken } from "@/lib/api";
import { useCart } from "@/context/CartContext";

/**
 * Renders the login and registration page with authentication controls.
 */
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

  const inputCls =
    "w-full rounded-xl border border-line p-3 outline-none focus:border-brand focus:ring-2 focus:ring-brand/20";

  return (
    <div className="mx-auto max-w-sm space-y-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <span className="grid h-12 w-12 place-items-center rounded-2xl bg-ink text-brand-light">
          <Coffee className="h-6 w-6" />
        </span>
        <h1 className="text-2xl font-extrabold text-ink">
          {mode === "login" ? "تسجيل الدخول" : "إنشاء حساب"}
        </h1>
      </div>

      <form onSubmit={submit} className="space-y-4 rounded-2xl border border-line bg-white p-6 shadow-card">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="البريد الإلكتروني"
          className={inputCls}
        />
        <input
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="كلمة المرور"
          className={inputCls}
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          disabled={busy}
          className="w-full rounded-xl bg-brand-dark py-3 font-semibold text-white hover:bg-ink disabled:opacity-50"
        >
          {busy ? "…" : mode === "login" ? "دخول" : "تسجيل"}
        </button>
        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="w-full text-sm font-medium text-brand hover:underline"
        >
          {mode === "login" ? "ليس لديك حساب؟ سجّل الآن" : "لديك حساب؟ سجّل الدخول"}
        </button>
      </form>

      <p className="text-center text-xs text-muted">
        حساب تجريبي: demo@example.com / demo1234 — للإدارة: admin@example.com / admin1234
      </p>
    </div>
  );
}
