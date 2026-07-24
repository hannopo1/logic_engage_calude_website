import type { Metadata } from "next";
import { Almarai } from "next/font/google";

import { Suspense } from "react";

import "./globals.css";
import AiAssistant from "@/components/AiAssistant";
import Footer from "@/components/Footer";
import Navbar from "@/components/Navbar";
import Tracker from "@/components/Tracker";
import { CartProvider } from "@/context/CartContext";

const almarai = Almarai({
  subsets: ["arabic"],
  weight: ["300", "400", "700", "800"],
  variable: "--font-almarai",
  display: "swap",
});

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
    <html lang="ar" dir="rtl" className={almarai.variable}>
      <body className="flex min-h-dvh flex-col font-sans">
        <CartProvider>
          <Suspense fallback={null}>
            <Tracker />
          </Suspense>
          <Navbar />
          <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:py-10">{children}</main>
          <Footer />
          <AiAssistant />
        </CartProvider>
      </body>
    </html>
  );
}
