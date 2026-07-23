import type { Metadata } from "next";

import "./globals.css";
import AiAssistant from "@/components/AiAssistant";
import Navbar from "@/components/Navbar";
import { CartProvider } from "@/context/CartContext";

export const metadata: Metadata = {
  title: "CaveBrew — Specialty Coffee & Brewing Gear",
  description: "AI-powered specialty coffee store. Modular headless commerce MVP.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <CartProvider>
          <Navbar />
          <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
          <AiAssistant />
        </CartProvider>
      </body>
    </html>
  );
}
