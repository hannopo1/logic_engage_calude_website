# API Reference (v1)

Base URL: `http://localhost:8000/api/v1` · Interactive docs: `http://localhost:8000/docs`

Auth uses a Bearer JWT (`Authorization: Bearer <token>`). Guest carts use an
`X-Session-Id: <uuid>` header instead.

## Auth
| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/auth/register` | `{email, password, first_name?, last_name?}` | returns `{access_token, user}` |
| POST | `/auth/login` | `{email, password}` | returns `{access_token, user}` |
| GET | `/auth/me` | — | requires auth |

## Catalog
| Method | Path | Notes |
|--------|------|-------|
| GET | `/categories` | list all categories |
| GET | `/products` | query: `category`, `min_price`, `max_price`, `page`, `page_size` |
| GET | `/products/{slug}` | product detail |
| GET | `/search?q=` | full-text search (natural phrases supported) |

## Cart
Send `X-Session-Id` (guest) or `Authorization` (user).
| Method | Path | Body |
|--------|------|------|
| GET | `/cart` | — |
| POST | `/cart/items` | `{product_id, quantity}` |
| PATCH | `/cart/items/{product_id}` | `{quantity}` (0 removes) |
| DELETE | `/cart/items/{product_id}` | — |

## Orders
| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/orders` | `{shipping_address?}` | converts the current cart; 409 if stock is insufficient |
| GET | `/orders` | — | requires auth; the user's orders |
| GET | `/orders/{id}` | — | requires auth |

## AI
| Method | Path | Body | Notes |
|--------|------|------|-------|
| POST | `/ai/chat` | `{message, history?}` | returns `{reply, provider, products[]}` |
| GET | `/ai/recommend/{product_id}` | — | returns `{similar[], also_bought[]}` |

## Meta
| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | `{status, ai_provider}` |
| GET | `/` | service info |

Every schema and example is available live in Swagger at `/docs`.

---

## Phase 2 — fulfillment & operator API

### Customer
| Method | Path | Notes |
|--------|------|-------|
| POST | `/orders` | now accepts `{payment_method}` (cod default; gateway declines until configured) |
| GET | `/orders/{id}/timeline` | sanitized Arabic fulfillment steps (no supplier/cost data) |

### Operator (admin role required — 403 otherwise)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/admin/dashboard` | PO counts by status, orders today, revenue, est. margin |
| GET | `/admin/purchase-orders?status=` | list POs (denormalized for the console) |
| POST | `/admin/purchase-orders/{id}/approve` | hand to purchasing agent → purchase package |
| POST | `/admin/purchase-orders/{id}/reject` | `{note, cancel}` → cancel or back to sourcing |
| POST | `/admin/purchase-orders/{id}/resource` | re-run sourcing for a pending PO |
| POST | `/admin/purchase-orders/{id}/mark-purchased` | `{supplier_order_ref, actual_cost?}` |
| POST | `/admin/purchase-orders/{id}/ship` | `{tracking_no, carrier?}` |
| POST | `/admin/purchase-orders/{id}/deliver` | mark delivered → order completed |
| GET/POST/PATCH | `/admin/suppliers` · `/admin/offers` | manage suppliers & sourcing offers |

---

## Phase 3 — merchant console & analytics

### Public
| Method | Path | Notes |
|--------|------|-------|
| POST | `/events` | ingest a storefront analytics event (anonymous, X-Session-Id) |

### Operator (admin role)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/admin/products` | list all products (incl. inactive) with offer counts |
| POST | `/admin/products` | create a product (dropship or own_stock; slug auto-derived) |
| PATCH | `/admin/products/{id}` | edit price/stock/type/active/… |
| GET | `/admin/offers?product_id=` | supplier offers for a product |
| POST | `/admin/offers` | attach an Amazon/Noon/… offer (url + cost) |
| GET | `/admin/customers` | customers with order count + total spent |
| GET | `/admin/analytics?days=` | visitor funnel, top products/searches, conversion |

---

## Phase 4 — discount coupons

### Public
| Method | Path | Notes |
|--------|------|-------|
| POST | `/coupons/validate` | `{code, subtotal}` → `{code, kind, discount, new_total}`; 404/400 if invalid, inactive, expired, exhausted, or below `min_order` |
| POST | `/orders` | now also accepts `{coupon_code}`; discount is re-validated & applied server-side, `used_count` incremented, payment authorized on the discounted total |

`OrderOut` gains `discount_amount` and `coupon_code`.

### Operator (admin role)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/admin/coupons` | list all coupons (active + inactive) |
| POST | `/admin/coupons` | create `{code, kind: percent\|fixed, value, min_order?, max_uses?, expires_at?}`; duplicate code → 409 |
| PATCH | `/admin/coupons/{id}` | edit value/limits or toggle `is_active` |

---

## Phase 5 — product reviews (verified purchase + moderation)

### Public
| Method | Path | Notes |
|--------|------|-------|
| GET | `/products/{slug}/reviews` | `{summary:{average,count,distribution}, items:[…]}` — approved reviews only |
| POST | `/products/{id}/reviews` | auth required; `{rating 1-5, title?, body}`. **403** unless the user bought the product; **409** if they already reviewed it. Created hidden (awaits moderation). |

`ProductOut` (list + detail) gains `rating_avg` and `rating_count` (approved reviews).

### Operator (admin role)
| Method | Path | Notes |
|--------|------|-------|
| GET | `/admin/reviews?status=pending\|all` | moderation queue |
| POST | `/admin/reviews/{id}/approve` | publish the review |
| POST | `/admin/reviews/{id}/reject` | delete the review |
