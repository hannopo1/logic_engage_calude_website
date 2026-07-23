# Architecture

The platform follows the Phase-1 design from the product roadmap: **API-first,
AI-first, modular, headless**. This document describes what is implemented in the
MVP foundation.

## Layers

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (headless storefront)                          │
│  Next.js 14 App Router · TypeScript · Tailwind           │
│  Pages: home, products, product, cart, checkout, login   │
│  Widget: AI shopping assistant                           │
└───────────────┬─────────────────────────────────────────┘
                │ REST (JSON) over /api/v1
┌───────────────▼─────────────────────────────────────────┐
│  Backend (FastAPI)                                       │
│  api/v1: auth, categories, products, search, cart,       │
│          orders, ai                                      │
│  services: cart_service, order_service                   │
│  ai: base(factory) → stub | anthropic | openai           │
│  core: config, database, security (JWT + bcrypt)         │
└───────┬───────────────────────────┬─────────────────────┘
        │ SQLAlchemy 2 / Alembic     │ (cache-ready)
┌───────▼──────────┐        ┌────────▼─────────┐
│  PostgreSQL 16   │        │  Redis 7         │
│  + full-text     │        │  sessions/cache  │
└──────────────────┘        └──────────────────┘
```

## Key decisions

- **Headless:** the frontend only talks to the REST API; any client (web, future
  mobile) can reuse the same surface. OpenAPI is auto-published at `/docs`.
- **Pluggable AI (`app/ai/base.py`):** a factory selects the provider from
  `AI_PROVIDER`. The default `stub` is grounded (RAG-lite) on the live catalog and
  needs no key or budget. `anthropic`/`openai` activate only when a key is present,
  and fall back to the stub on misconfiguration — the platform never hard-fails.
- **Full-text search in Postgres:** a `STORED GENERATED` `tsvector` column on
  `products`, kept in sync by the database itself (no triggers, no app code), with a
  GIN index. Upgrade path to semantic search via `pgvector` is noted in the roadmap.
- **Cart ownership:** a cart is resolved by the logged-in user, or by an
  `X-Session-Id` header for guests, so anonymous shopping works before sign-up.
- **Atomic checkout (`order_service.py`):** stock is validated for every line before
  any write; the order is created and stock decremented in one transaction; the cart
  is emptied on success. Over-ordering returns HTTP 409.

## Request lifecycle (example: add to cart)

1. Browser calls `POST /api/v1/cart/items` with `X-Session-Id` (guest) or `Authorization` (user).
2. `deps.get_current_user_optional` resolves the user (or none).
3. `cart_service.get_or_create_cart` finds/creates the cart.
4. `cart_service.add_item` validates the product and upserts the line.
5. The serialized cart (items, subtotal, count) is returned.

## Extending

Add a new domain (e.g. reviews):
1. Create `app/models/review.py`, import it in `app/models/__init__.py`.
2. `make revision m="add reviews"` then `make migrate`.
3. Add `app/schemas/review.py`, a router in `app/api/v1/reviews.py`, register it in
   `app/api/v1/__init__.py`.

The modular boundaries mean new modules do not touch existing ones.
