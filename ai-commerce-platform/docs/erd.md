# Database Schema (ERD)

MVP tables implemented in migration `0001_init`. The design mirrors Phase-1 of the
roadmap; deferred tables are listed at the bottom.

```
users                      categories                 products
──────────────             ──────────────             ──────────────
id (PK)                    id (PK)                     id (PK)
email (uniq)               name                        name
password_hash              slug (uniq)                 slug (uniq)
first_name                 parent_id → categories.id   description
last_name                  image                       price
phone                                                  cost_price
role                                                   sku (uniq)
is_active                                              stock_qty
created_at                                             image
                                                       tags            ← recommender
                                                       category_id → categories.id
                                                       is_active
                                                       seo_title
                                                       created_at
                                                       search_vector   ← GENERATED tsvector (GIN)

carts                      cart_items                  orders
──────────────             ──────────────             ──────────────
id (PK)                    id (PK)                     id (PK)
user_id → users.id         cart_id → carts.id          user_id → users.id
session_id                 product_id → products.id    status
created_at                 quantity                    payment_status
                           UNIQUE(cart_id,product_id)  total_amount
                                                       shipping_address
order_items                                            created_at
──────────────
id (PK)
order_id → orders.id
product_id → products.id
product_name   ← snapshot at purchase
quantity
unit_price     ← snapshot
total_price
```

## Notes

- **`products.search_vector`** is a Postgres `STORED GENERATED` column computed from
  `name + description + tags`, indexed with GIN. The database maintains it; no
  application code writes it. In the ORM it is declared `Computed(...)` so inserts
  never touch it.
- **Snapshots** on `order_items` (`product_name`, `unit_price`) preserve the order's
  historical truth even if the product later changes or is deleted.
- **Cart identity** supports both a `user_id` (authenticated) and a `session_id`
  (guest), enabling pre-login shopping.

## Deferred to later phases (see roadmap)

`brands`, `reviews`, `wishlist`, `addresses`, `payments`, `shipments`, `coupons`,
`inventory_log`, `order_status_history`, `analytics_events`, and a `pgvector`
embedding column for semantic search. The modular schema admits these as additive
migrations without altering existing tables.

---

## Phase 2 — drop-shipping tables (migration `0002`)

```
suppliers                  supplier_offers            purchase_orders
──────────────             ──────────────             ──────────────
id (PK)                    id (PK)                    id (PK)
name                       product_id → products.id   order_id → orders.id
slug (uniq)                supplier_id → suppliers.id  order_item_id → order_items.id
kind (marketplace|         url                        supplier_offer_id → supplier_offers.id
      classifieds)         external_sku               status  ← PO state machine
region (EG)                supplier_price             quantity
mode (manual|              shipping_cost              expected_cost / actual_cost
      assisted|api)        currency (EGP)             supplier_order_ref
website                    lead_time_days             tracking_no / carrier
is_active                  is_active                  created_at / updated_at

purchase_order_events (append-only audit)
──────────────
id (PK) · purchase_order_id → purchase_orders.id · status · note · actor (agent|operator|system) · created_at

orders  +column: payment_method (cod|gateway)
products.search_vector  → regenerated with 'simple' tsconfig (Arabic-friendly)
```

- **landed cost** = `supplier_price + shipping_cost`; the sourcing agent picks the
  cheapest active offer whose margin vs the selling price ≥ `MARGIN_MIN_PERCENT`.
- One `purchase_order` per order item; the parent order's status is derived from its
  POs by `fulfillment_service.sync_order_status`.

---

## Phase 3 — merchant console (migration `0003`)

```
products  +column: fulfillment_type (dropship|own_stock)
          own_stock items are fulfilled from the merchant's own inventory
          (the sourcing agent opens a ready-to-ship PO, no supplier)

analytics_events
──────────────
id (PK) · event_type (page_view|product_view|search|add_to_cart|begin_checkout|purchase)
session_id · user_id → users.id · path · product_id → products.id · query · created_at
```
Written by the public `POST /events` endpoint (anonymous, keyed by X-Session-Id).

---

## Phase 4 — discount coupons (migration `0004`)

```
coupons
──────────────
id (PK) · code (uniq) · kind (percent|fixed) · value · min_order
max_uses · used_count · is_active · expires_at · created_at

orders  +columns: discount_amount (default 0) · coupon_code
```

- A coupon is valid when active, not expired, under `max_uses`, and the cart
  subtotal ≥ `min_order`. `POST /coupons/validate` previews the discount; the
  discount is **re-computed and re-validated** at checkout, so the client value is
  never trusted. `used_count` is incremented atomically when the order is placed.
- `orders.total_amount` stores the **discounted** total; `discount_amount` and
  `coupon_code` record what was applied for the receipt and reporting.

---

## Phase 5 — product reviews (migration `0005`)

```
reviews
──────────────
id (PK) · product_id → products.id (CASCADE) · user_id → users.id (CASCADE)
order_id → orders.id (SET NULL, proof of purchase)
rating (1..5) · title · body · is_verified · is_approved · created_at
UNIQUE(product_id, user_id)   ← one review per customer per product
```

- **Verified purchase gate:** a review can be created only when the user has an
  `order_items` row for that product (join through `orders.user_id`). So every
  review is a verified purchase; `order_id` records which order proved it.
- **Moderation:** reviews are created with `is_approved=false` and appear on the
  storefront only after an operator approves them. `rating_avg`/`rating_count`
  exposed on products aggregate **approved** reviews only.
