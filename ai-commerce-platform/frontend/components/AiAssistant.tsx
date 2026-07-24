"use client";

import { MessageCircle, Send, X } from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

/**
 * Renders a toggleable shopping assistant chat interface.
 *
 * @returns The shopping assistant launcher and chat panel.
 */
export default function AiAssistant() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "أهلاً! أنا مساعد التسوّق. اسألني عن أدوات القهوة — مثلاً «مطحنة للإسبريسو تحت 5000 جنيه».",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    const history = msgs.map((m) => ({ role: m.role, content: m.content }));
    setMsgs((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await api.chat(text, history);
      setMsgs((m) => [...m, { role: "assistant", content: res.reply }]);
    } catch (e) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: `Sorry — ${(e as Error).message}` },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "إغلاق المساعد" : "اسأل المساعد"}
        className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full bg-brand-dark px-5 py-3 font-semibold text-white shadow-lift hover:bg-ink"
      >
        {open ? <X className="h-5 w-5" /> : <MessageCircle className="h-5 w-5" />}
        {open ? "إغلاق" : "اسأل المساعد"}
      </button>

      {open && (
        <div className="fixed bottom-20 right-5 z-50 flex h-[28rem] w-80 flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-lift">
          <div className="flex items-center gap-2 bg-ink px-4 py-3 font-semibold text-white">
            <MessageCircle className="h-4 w-4 text-brand-light" />
            مساعد التسوّق
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto p-3 text-sm">
            {msgs.map((m, i) => (
              <div
                key={i}
                className={m.role === "user" ? "text-right" : "text-left"}
              >
                <span
                  className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 ${
                    m.role === "user"
                      ? "bg-brand-dark text-white"
                      : "bg-stone-100 text-ink"
                  }`}
                >
                  {m.content}
                </span>
              </div>
            ))}
            {busy && <div className="text-stone-400">جارٍ التفكير…</div>}
          </div>
          <div className="flex gap-2 border-t border-line p-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="اكتب سؤالك…"
              className="flex-1 rounded-xl border border-line px-3 py-2 text-sm outline-none focus:border-brand"
            />
            <button
              onClick={send}
              disabled={busy}
              aria-label="إرسال"
              className="grid place-items-center rounded-xl bg-brand-dark px-3 text-white hover:bg-ink disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
