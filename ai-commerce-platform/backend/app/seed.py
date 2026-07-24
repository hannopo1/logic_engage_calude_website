"""Seed the demo store: specialty coffee gear for the Egyptian market (EGP).

Drop-shipping model — no warehouse stock. Each product carries supplier offers
(Jumia/Amazon/Noon/OLX Egypt) that the sourcing agent picks from when a real
order lands. One product (المطحنة اليدوية) is intentionally seeded with only
low-margin offers so the pending_sourcing operator flow can be demonstrated.

Idempotent — running twice will not duplicate rows. Run with:
    python -m app.seed        (inside the backend container: `make seed`)
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.supplier import Supplier, SupplierOffer
from app.models.user import User

CATEGORIES = [
    ("ماكينات إسبريسو", "espresso-machines"),
    ("مطاحن قهوة", "grinders"),
    ("أدوات تحضير", "brewers-drippers"),
    ("بن مختص", "coffee-beans"),
    ("إكسسوارات", "accessories"),
]

# (name, slug, description, selling_price_EGP, sku, stock, tags, category_slug)
PRODUCTS = [
    ("ماكينة إسبريسو باريستا برو", "barista-pro-espresso",
     "ماكينة إسبريسو بغلايتين وتحكم PID في درجة الحرارة — جودة الكافيهات في بيتك.",
     "36500", "ESP-001", 15, "اسبريسو,ماكينة,espresso,machine,pid", "espresso-machines"),
    ("ماكينة إسبريسو كومباكت", "compact-espresso",
     "ماكينة بغلاية واحدة وحجم صغير مثالي للمطابخ الصغيرة وللمبتدئين.",
     "15900", "ESP-002", 20, "اسبريسو,ماكينة,صغيرة,espresso,compact", "espresso-machines"),
    ("مطحنة قهوة احترافية", "precision-burr-grinder",
     "مطحنة بشفرات مخروطية 40 مم و40 درجة طحن من الإسبريسو حتى الفرنش برس.",
     "9200", "GRD-001", 30, "مطحنة,طحن,grinder,burr,conical", "grinders"),
    ("مطحنة يدوية للسفر", "hand-grinder-travel",
     "مطحنة يدوية استانلس بشفرات سيراميك — رفيقة السفر المثالية.",
     "3300", "GRD-002", 45, "مطحنة,يدوية,سفر,grinder,manual,travel", "grinders"),
    ("قمع ترشيح V60", "pour-over-v60",
     "قمع سيراميك مخروطي لقهوة مقطرة نظيفة ومشرقة — كوب واحد.",
     "1150", "BRW-001", 80, "ترشيح,مقطرة,v60,pour-over,dripper", "brewers-drippers"),
    ("فرنش برس 1 لتر", "french-press-1l",
     "فرنش برس زجاج بوروسيليكات بفلتر استانلس، سعة لتر.",
     "1850", "BRW-002", 60, "فرنش برس,french-press,immersion", "brewers-drippers"),
    ("إيروبرس", "aeropress-brewer",
     "أداة تحضير سريعة بالضغط والنقع لقهوة ناعمة قليلة الحموضة.",
     "1700", "BRW-003", 55, "ايروبرس,aeropress,سريعة,portable", "brewers-drippers"),
    ("بن إثيوبيا يرغاتشيف 250 جم", "ethiopia-yirgacheffe-250g",
     "تحميص فاتح أحادي المصدر بنكهات زهرية وحمضيات — حبوب كاملة.",
     "850", "BEAN-001", 100, "بن,اثيوبيا,تحميص فاتح,beans,single-origin", "coffee-beans"),
    ("بن كولومبيا سوبريمو 250 جم", "colombia-supremo-250g",
     "تحميص متوسط متوازن بحلاوة الكراميل — حبوب كاملة.",
     "750", "BEAN-002", 120, "بن,كولومبيا,كراميل,beans,medium-roast", "coffee-beans"),
    ("خلطة إسبريسو 1 كجم", "espresso-blend-1kg",
     "تحميص غامق مخصص للإسبريسو — قوام شوكولاتة ومكسرات. كيلو كامل.",
     "2000", "BEAN-003", 70, "بن,خلطة,اسبريسو,beans,blend,dark-roast", "coffee-beans"),
    ("ميزان قهوة بدقة 0.1 جم", "precision-scale",
     "ميزان قهوة بدقة 0.1 جم ومؤقّت تحضير مدمج.",
     "2300", "ACC-001", 40, "ميزان,مؤقت,scale,timer,precision", "accessories"),
    ("غلاية رقبة الإوزة 1 لتر", "gooseneck-kettle-1l",
     "غلاية بصنبور رقبة الإوزة وتحكم في درجة الحرارة لصب مثالي.",
     "4200", "ACC-002", 35, "غلاية,رقبة الاوزة,kettle,gooseneck", "accessories"),
]

SUPPLIERS = [
    # (name, slug, kind, mode, website, notes)
    ("جوميا مصر", "jumia-eg", "marketplace", "assisted", "https://www.jumia.com.eg",
     "شراء مساعَد من حساب الشركة. التحويل لوضع api يتطلب حساب شريك رسمي."),
    ("أمازون مصر", "amazon-eg", "marketplace", "assisted", "https://www.amazon.eg",
     "المسار الرسمي للأتمتة: Amazon Business API — يتطلب حساب أعمال."),
    ("نون مصر", "noon-eg", "marketplace", "assisted", "https://www.noon.com/egypt-ar",
     "المسار الرسمي للأتمتة: تكاملات نون للشركاء."),
    ("أولكس مصر", "olx-eg", "classifieds", "manual", "https://www.dubizzle.com.eg",
     "إعلانات أفراد (مستعمل/جديد) — لا يوجد API شراء؛ تنفيذ يدوي دائماً."),
]

# slug → list of (supplier_slug, supplier_price, shipping, lead_days, url_path)
# Margins vs selling price are healthy (>15%) except hand-grinder-travel,
# which is deliberately low-margin to demo the pending_sourcing flow.
OFFERS: dict[str, list[tuple[str, str, str, int, str]]] = {
    "barista-pro-espresso": [
        ("amazon-eg", "27500", "150", 3, "/dp/ESP001"),
        ("noon-eg", "28900", "0", 4, "/p/esp001"),
        ("jumia-eg", "29900", "75", 5, "/esp001.html"),
    ],
    "compact-espresso": [
        ("jumia-eg", "12400", "75", 4, "/esp002.html"),
        ("amazon-eg", "12900", "150", 3, "/dp/ESP002"),
    ],
    "precision-burr-grinder": [
        ("noon-eg", "6900", "0", 4, "/p/grd001"),
        ("amazon-eg", "7250", "150", 3, "/dp/GRD001"),
        ("olx-eg", "5800", "120", 6, "/ad/grd001"),
    ],
    "hand-grinder-travel": [
        # low margin on purpose (selling 3300; landed ≈ 3080/3170 → <15%)
        ("jumia-eg", "3020", "60", 5, "/grd002.html"),
        ("noon-eg", "3170", "0", 4, "/p/grd002"),
    ],
    "pour-over-v60": [
        ("amazon-eg", "780", "70", 3, "/dp/BRW001"),
        ("jumia-eg", "820", "60", 5, "/brw001.html"),
    ],
    "french-press-1l": [
        ("noon-eg", "1290", "0", 4, "/p/brw002"),
        ("jumia-eg", "1350", "60", 5, "/brw002.html"),
    ],
    "aeropress-brewer": [
        ("amazon-eg", "1250", "70", 3, "/dp/BRW003"),
    ],
    "ethiopia-yirgacheffe-250g": [
        ("noon-eg", "590", "0", 4, "/p/bean001"),
        ("jumia-eg", "620", "50", 5, "/bean001.html"),
    ],
    "colombia-supremo-250g": [
        ("jumia-eg", "520", "50", 5, "/bean002.html"),
        ("amazon-eg", "545", "70", 3, "/dp/BEAN002"),
    ],
    "espresso-blend-1kg": [
        ("amazon-eg", "1400", "70", 3, "/dp/BEAN003"),
        ("noon-eg", "1480", "0", 4, "/p/bean003"),
    ],
    "precision-scale": [
        ("noon-eg", "1650", "0", 4, "/p/acc001"),
        ("olx-eg", "1300", "100", 7, "/ad/acc001"),
    ],
    "gooseneck-kettle-1l": [
        ("jumia-eg", "3050", "75", 5, "/acc002.html"),
        ("amazon-eg", "3150", "150", 3, "/dp/ACC002"),
    ],
}

# Demo orders to power the "customers also bought" recommender.
DEMO_ORDERS = [
    ["barista-pro-espresso", "precision-burr-grinder", "espresso-blend-1kg"],
    ["pour-over-v60", "gooseneck-kettle-1l", "ethiopia-yirgacheffe-250g"],
    ["precision-burr-grinder", "precision-scale"],
    ["barista-pro-espresso", "precision-scale", "espresso-blend-1kg"],
    ["french-press-1l", "colombia-supremo-250g"],
]


def run() -> None:
    """
    Seed the database with the demo catalog, suppliers, offers, users, and completed orders.
    
    The operation is skipped when the catalog already contains a product. Demo users are created only when their email addresses are absent.
    """
    db = SessionLocal()
    try:
        if db.scalar(select(Product).limit(1)):
            print("Catalog already seeded — skipping.")
            return

        # Categories
        cat_by_slug: dict[str, Category] = {}
        for name, slug in CATEGORIES:
            cat = Category(name=name, slug=slug)
            db.add(cat)
            cat_by_slug[slug] = cat
        db.flush()

        # Products (selling prices in EGP)
        prod_by_slug: dict[str, Product] = {}
        for name, slug, desc, price, sku, stock, tags, cat_slug in PRODUCTS:
            p = Product(
                name=name,
                slug=slug,
                description=desc,
                price=Decimal(price),
                cost_price=None,  # cost comes from supplier offers in drop-shipping
                sku=sku,
                stock_qty=stock,
                tags=tags,
                category_id=cat_by_slug[cat_slug].id,
                seo_title=name,
            )
            db.add(p)
            prod_by_slug[slug] = p
        db.flush()

        # Suppliers
        sup_by_slug: dict[str, Supplier] = {}
        for name, slug, kind, mode, website, notes in SUPPLIERS:
            s = Supplier(name=name, slug=slug, kind=kind, mode=mode, website=website, notes=notes)
            db.add(s)
            sup_by_slug[slug] = s
        db.flush()

        # Supplier offers
        n_offers = 0
        for product_slug, offers in OFFERS.items():
            product = prod_by_slug[product_slug]
            for supplier_slug, sprice, shipping, lead, path in offers:
                supplier = sup_by_slug[supplier_slug]
                db.add(
                    SupplierOffer(
                        product_id=product.id,
                        supplier_id=supplier.id,
                        url=(supplier.website or "") + path,
                        external_sku=f"{supplier_slug.upper()}-{product.sku}",
                        supplier_price=Decimal(sprice),
                        shipping_cost=Decimal(shipping),
                        currency="EGP",
                        lead_time_days=lead,
                    )
                )
                n_offers += 1

        # Users: demo customer + operator admin
        if not db.scalar(select(User).where(User.email == "demo@example.com")):
            db.add(
                User(
                    email="demo@example.com",
                    password_hash=hash_password("demo1234"),
                    first_name="عميل",
                    last_name="تجريبي",
                    role="customer",
                )
            )
        if not db.scalar(select(User).where(User.email == "admin@example.com")):
            db.add(
                User(
                    email="admin@example.com",
                    password_hash=hash_password("admin1234"),
                    first_name="مشغّل",
                    last_name="المنصة",
                    role="admin",
                )
            )

        # Demo completed orders (feed the recommender only — no POs needed).
        for slugs in DEMO_ORDERS:
            total = Decimal("0")
            order = Order(status="completed", payment_status="paid", total_amount=Decimal("0"))
            db.add(order)
            db.flush()
            for s in slugs:
                p = prod_by_slug[s]
                line = Decimal(str(p.price))
                total += line
                db.add(
                    OrderItem(
                        order_id=order.id,
                        product_id=p.id,
                        product_name=p.name,
                        quantity=1,
                        unit_price=line,
                        total_price=line,
                    )
                )
            order.total_amount = total

        db.commit()
        print(
            f"Seeded {len(CATEGORIES)} categories, {len(PRODUCTS)} products, "
            f"{len(SUPPLIERS)} suppliers, {n_offers} offers, {len(DEMO_ORDERS)} demo orders.\n"
            f"Users: demo@example.com/demo1234 (customer), admin@example.com/admin1234 (operator)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
