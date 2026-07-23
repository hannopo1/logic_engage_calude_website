# AI Commerce Platform — Drop-shipping Store (Egypt)

An **AI-first, modular, headless** e-commerce platform running a **zero-inventory
drop-shipping** model for the Egyptian market: an Arabic (RTL) storefront priced in
EGP, and **purchasing agents** that source each sold item from Jumia / Amazon / Noon /
OLX Egypt and ship it to the customer — with a **human-approval gate** before any buy.

> Zero-budget by design: every component is open-source; the AI assistant works with
> **no API key** (a grounded stub), and the store launches on **cash-on-delivery** with
> no payment-gateway account required.

> **Compliance:** the platform never scripts/scrapes a supplier's checkout (ToS/ban
> risk). Agents automate everything up to the purchase, then an operator confirms.
> Full automation is available only through official supplier APIs — see
> [`docs/dropshipping.md`](docs/dropshipping.md).

---

## What works today

| Area | Feature |
|------|---------|
| Storefront | Arabic RTL, EGP pricing, home / catalog / product / cart |
| Auth | Register / login (JWT), roles (customer / operator) |
| Search | PostgreSQL full-text (Arabic-friendly `simple` config) + GIN |
| Cart | Guest (session) + user carts |
| Checkout | Cash-on-delivery; pluggable gateway layer (Paymob/Stripe-ready) |
| **Drop-shipping** | Sourcing agent picks cheapest supplier meeting a margin floor → purchase order per item |
| **Purchasing agent** | `assisted` (operator-approved) · `simulation` (auto, $0) · `api` (official connectors) |
| **Operator console** | `/admin`: approve/reject POs, purchase package, mark purchased/shipped/delivered, dashboard |
| Order tracking | Sanitized Arabic timeline (no supplier/cost leakage) |
| AI assistant | `/ai/chat` grounded in the catalog (Arabic; stub default, pluggable LLM) |
| Recommendations | "Similar" (content) + "Also bought" (co-occurrence) |
| Docs | Auto OpenAPI/Swagger at `/docs` |

Deferred (see [`docs/roadmap.md`](docs/roadmap.md) & [`docs/launch.md`](docs/launch.md)):
live payment gateway, official supplier API connectors, reviews/wishlist/coupons,
mobile apps, semantic (pgvector) search, demand forecasting.

---

## Run it (one command)

Requires Docker + Docker Compose.

```bash
cp .env.example .env      # optional; `make up` does this for you
make up                   # build + start db, redis, backend, frontend
make seed                 # load the demo Arabic/EGP catalog + suppliers
```

Then open:
- **Storefront:** http://localhost:3000
- **Operator console:** http://localhost:3000/admin
- **API + Swagger docs:** http://localhost:8000/docs

Demo logins — customer: `demo@example.com` / `demo1234` · operator: `admin@example.com` / `admin1234`.

Try the full loop: buy something (COD) → open `/admin` → approve the auto-created
purchase order → follow the purchase package → mark purchased → ship → deliver.
Set `AGENT_MODE=simulation` in `.env` to auto-execute purchases for a hands-off demo.

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
