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
