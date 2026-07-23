"use client";

import { useState } from "react";

import { api } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

export default function AiAssistant() {
  const [open, setOpen] = useState(false);
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm your shopping assistant. Ask me about our coffee gear — e.g. \"a grinder for espresso under $200\".",
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
        className="fixed bottom-5 right-5 z-50 rounded-full bg-brand px-5 py-3 font-semibold text-white shadow-lg hover:bg-brand-dark"
      >
        {open ? "Close" : "💬 Ask AI"}
      </button>

      {open && (
        <div className="fixed bottom-20 right-5 z-50 flex h-[28rem] w-80 flex-col overflow-hidden rounded-xl border border-stone-200 bg-white shadow-2xl">
          <div className="bg-brand px-4 py-3 font-semibold text-white">
            Shopping Assistant
          </div>
          <div className="flex-1 space-y-3 overflow-y-auto p-3 text-sm">
            {msgs.map((m, i) => (
              <div
                key={i}
                className={m.role === "user" ? "text-right" : "text-left"}
              >
                <span
                  className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 ${
                    m.role === "user"
                      ? "bg-brand text-white"
                      : "bg-stone-100 text-stone-800"
                  }`}
                >
                  {m.content}
                </span>
              </div>
            ))}
            {busy && <div className="text-stone-400">Thinking…</div>}
          </div>
          <div className="flex gap-2 border-t border-stone-200 p-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Type a question…"
              className="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm outline-none focus:border-brand"
            />
            <button
              onClick={send}
              disabled={busy}
              className="rounded-md bg-brand px-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}
