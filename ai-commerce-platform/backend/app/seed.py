"""Seed a demo niche catalog: specialty coffee & brewing gear.

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
from app.models.user import User

CATEGORIES = [
    ("Espresso Machines", "espresso-machines"),
    ("Grinders", "grinders"),
    ("Brewers & Drippers", "brewers-drippers"),
    ("Coffee Beans", "coffee-beans"),
    ("Accessories", "accessories"),
]

# (name, slug, description, price, cost, sku, stock, tags, category_slug)
PRODUCTS = [
    ("Barista Pro Espresso Machine", "barista-pro-espresso", "Dual-boiler espresso machine with PID temperature control for cafe-quality shots at home.", "749.00", "480.00", "ESP-001", 12, "espresso,machine,dual-boiler,pid", "espresso-machines"),
    ("Compact Espresso Machine", "compact-espresso", "Single-boiler machine with a compact footprint, ideal for small kitchens.", "329.00", "205.00", "ESP-002", 20, "espresso,machine,compact,beginner", "espresso-machines"),
    ("Precision Burr Grinder", "precision-burr-grinder", "40mm conical burr grinder with 40 grind settings from espresso to French press.", "189.00", "110.00", "GRD-001", 30, "grinder,burr,conical,adjustable", "grinders"),
    ("Hand Grinder Travel", "hand-grinder-travel", "Portable stainless-steel hand grinder with ceramic burrs for travel.", "69.00", "34.00", "GRD-002", 45, "grinder,manual,travel,ceramic", "grinders"),
    ("Pour-Over Dripper V60", "pour-over-v60", "Ceramic cone dripper for clean, bright pour-over coffee. Single-cup.", "24.00", "9.00", "BRW-001", 80, "pour-over,dripper,ceramic,manual", "brewers-drippers"),
    ("French Press 1L", "french-press-1l", "Borosilicate glass French press with stainless filter, 1 litre.", "39.00", "18.00", "BRW-002", 60, "french-press,immersion,glass", "brewers-drippers"),
    ("AeroPress Brewer", "aeropress-brewer", "Fast immersion + pressure brewer for smooth, low-acidity coffee.", "34.00", "16.00", "BRW-003", 55, "aeropress,immersion,portable", "brewers-drippers"),
    ("Ethiopia Yirgacheffe Beans 250g", "ethiopia-yirgacheffe-250g", "Light-roast single origin with floral and citrus notes. Whole bean.", "18.00", "8.00", "BEAN-001", 100, "beans,single-origin,light-roast,floral", "coffee-beans"),
    ("Colombia Supremo Beans 250g", "colombia-supremo-250g", "Medium-roast, balanced with caramel sweetness. Whole bean.", "16.00", "7.00", "BEAN-002", 120, "beans,single-origin,medium-roast,caramel", "coffee-beans"),
    ("Espresso Blend Beans 1kg", "espresso-blend-1kg", "Dark-roast blend built for espresso — chocolate and nutty body. 1kg.", "42.00", "20.00", "BEAN-003", 70, "beans,blend,dark-roast,espresso", "coffee-beans"),
    ("Precision Scale 0.1g", "precision-scale", "Coffee scale with 0.1g resolution and built-in brew timer.", "49.00", "24.00", "ACC-001", 40, "scale,timer,accessory,precision", "accessories"),
    ("Gooseneck Kettle 1L", "gooseneck-kettle-1l", "Variable-temperature gooseneck kettle for controlled pour-over flow.", "89.00", "48.00", "ACC-002", 35, "kettle,gooseneck,pour-over,temperature", "accessories"),
]

# Demo orders to power the "customers also bought" recommender.
# Each tuple is a list of product slugs bought together.
DEMO_ORDERS = [
    ["barista-pro-espresso", "precision-burr-grinder", "espresso-blend-1kg"],
    ["pour-over-v60", "gooseneck-kettle-1l", "ethiopia-yirgacheffe-250g"],
    ["precision-burr-grinder", "precision-scale"],
    ["barista-pro-espresso", "precision-scale", "espresso-blend-1kg"],
    ["french-press-1l", "colombia-supremo-250g"],
]


def run() -> None:
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

        # Products
        prod_by_slug: dict[str, Product] = {}
        for name, slug, desc, price, cost, sku, stock, tags, cat_slug in PRODUCTS:
            p = Product(
                name=name,
                slug=slug,
                description=desc,
                price=Decimal(price),
                cost_price=Decimal(cost),
                sku=sku,
                stock_qty=stock,
                tags=tags,
                category_id=cat_by_slug[cat_slug].id,
                seo_title=name,
            )
            db.add(p)
            prod_by_slug[slug] = p
        db.flush()

        # Demo user
        if not db.scalar(select(User).where(User.email == "demo@example.com")):
            db.add(
                User(
                    email="demo@example.com",
                    password_hash=hash_password("demo1234"),
                    first_name="Demo",
                    last_name="User",
                    role="customer",
                )
            )

        # Demo orders (feed the recommender). Stock intentionally not decremented here.
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
        print(f"Seeded {len(CATEGORIES)} categories, {len(PRODUCTS)} products, "
              f"{len(DEMO_ORDERS)} demo orders, 1 demo user (demo@example.com / demo1234).")
    finally:
        db.close()


if __name__ == "__main__":
    run()
