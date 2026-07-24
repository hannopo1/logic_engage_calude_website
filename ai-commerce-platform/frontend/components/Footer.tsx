import Link from "next/link";
import { Coffee, ShieldCheck, Truck, Wallet } from "lucide-react";

/**
 * Renders the site footer with brand information, store navigation, service highlights, contact details, and copyright information.
 */
export default function Footer() {
  return (
    <footer className="mt-16 border-t border-line bg-white">
      <div className="mx-auto max-w-6xl px-4 py-10">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="space-y-3">
            <Link href="/" className="flex items-center gap-2 text-lg font-extrabold text-ink">
              <span className="grid h-8 w-8 place-items-center rounded-xl bg-ink text-brand-light">
                <Coffee className="h-4 w-4" />
              </span>
              كيڤ برو
            </Link>
            <p className="text-sm leading-6 text-muted">
              قهوة مختصة وأدوات تحضير دقيقة — مع مساعد ذكي يرشّح لك ما يناسبك. توصيل لكل مصر.
            </p>
          </div>

          <div className="space-y-2 text-sm">
            <h3 className="font-bold text-ink">المتجر</h3>
            <Link href="/products" className="block text-muted hover:text-brand">كل المنتجات</Link>
            <Link href="/orders" className="block text-muted hover:text-brand">طلباتي</Link>
            <Link href="/cart" className="block text-muted hover:text-brand">السلة</Link>
          </div>

          <div className="space-y-2 text-sm">
            <h3 className="font-bold text-ink">لماذا كيڤ برو</h3>
            <p className="flex items-center gap-2 text-muted"><Truck className="h-4 w-4 text-brand" /> توصيل لكل المحافظات</p>
            <p className="flex items-center gap-2 text-muted"><Wallet className="h-4 w-4 text-brand" /> الدفع عند الاستلام</p>
            <p className="flex items-center gap-2 text-muted"><ShieldCheck className="h-4 w-4 text-brand" /> تقييمات حقيقية موثّقة</p>
          </div>

          <div className="space-y-2 text-sm">
            <h3 className="font-bold text-ink">تواصل</h3>
            <p className="text-muted">خدمة العملاء: كل يوم 10ص–10م</p>
            <p className="text-muted">القاهرة، مصر</p>
          </div>
        </div>

        <p className="mt-8 border-t border-line pt-6 text-center text-xs text-muted">
          © {new Date().getFullYear()} كيڤ برو — جميع الحقوق محفوظة.
        </p>
      </div>
    </footer>
  );
}
