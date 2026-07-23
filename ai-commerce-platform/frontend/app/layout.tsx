import type { Metadata } from "next";

import { Suspense } from "react";

import "./globals.css";
import AiAssistant from "@/components/AiAssistant";
import Navbar from "@/components/Navbar";
import Tracker from "@/components/Tracker";
import { CartProvider } from "@/context/CartContext";

export const metadata: Metadata = {
  title: "كيڤ برو — قهوة مختصة وأدوات تحضير",
  description: "متجر قهوة مختصة مدعوم بالذكاء الاصطناعي — توصيل لكل مصر، الدفع عند الاستلام.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <CartProvider>
          <Suspense fallback={null}>
            <Tracker />
          </Suspense>
          <Navbar />
          <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
          <AiAssistant />
        </CartProvider>
      </body>
    </html>
  );
}
