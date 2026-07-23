# AI Commerce Platform — MVP Foundation

An **AI-first, modular, headless** e-commerce platform. This repository is the
**Phase-1 MVP foundation**: a runnable monorepo you can start with one command and
grow toward the full roadmap (payments, marketplace, mobile, advanced AI).

> Built to be **zero-budget**: every component is open-source, and the AI assistant
> works with **no API key** (a grounded stub). Add an Anthropic/OpenAI key later to
> switch to a real LLM — no code changes.

---

## What works today

| Area | Feature |
|------|---------|
| Auth | Register / login (JWT), `GET /me` |
| Catalog | Categories, products (filter + pagination), product detail |
| Search | PostgreSQL full-text search (`tsvector` + GIN) with natural phrases |
| Cart | Add / update / remove; works for guests (session) and logged-in users |
| Checkout | Cart → order, atomic stock check + decrement |
| Orders | Order history, order detail |
| AI assistant | `/ai/chat` grounded in the catalog (stub by default, pluggable to a real LLM) |
| Recommendations | "Similar products" (content-based) + "Customers also bought" (co-occurrence) |
| Docs | Auto-generated OpenAPI/Swagger at `/docs` |

Deferred to later phases (documented in [`docs/roadmap.md`](docs/roadmap.md)):
real payments, shipping, reviews, wishlist, coupons, multi-vendor, mobile apps,
semantic (pgvector) search, demand forecasting.

---

## Run it (one command)

Requires Docker + Docker Compose.

```bash
cp .env.example .env      # optional; `make up` does this for you
make up                   # build + start db, redis, backend, frontend
make seed                 # load the demo coffee catalog
```

Then open:
- **Storefront:** http://localhost:3000
- **API + Swagger docs:** http://localhost:8000/docs

Demo account: `demo@example.com` / `demo1234`.

Stop with `make down`. See `make help` for all targets.

---

## Architecture (high level)

```
Next.js storefront ──HTTP──▶ FastAPI (REST /api/v1) ──▶ PostgreSQL
                                     │                    ▲
                                     ├─ AI layer (stub | anthropic | openai)
                                     └─ Redis (cache-ready)
```

- **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind.
- **Backend:** FastAPI + SQLAlchemy 2 + Alembic.
- **Database:** PostgreSQL 16 (full-text search built in).
- **AI:** pluggable provider (`app/ai/`), stub default, real LLM on key.

Full details in [`docs/architecture.md`](docs/architecture.md) and the schema in
[`docs/erd.md`](docs/erd.md).

---

## Enable a real AI model (optional)

Edit `.env`:

```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
# or:
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

Restart the backend. The assistant and its grounding context are unchanged — only
the answer generation swaps to the real model.

---

## Development

```bash
# Backend tests (no DB needed for the smoke suite)
make test

# New DB migration after changing models
make revision m="add reviews table"
make migrate
```

Layout:

```
backend/   FastAPI app (app/), Alembic migrations, tests
frontend/  Next.js storefront
docs/      architecture, ERD, API summary, roadmap
```
