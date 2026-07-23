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
