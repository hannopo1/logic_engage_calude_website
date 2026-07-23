# Roadmap — beyond the MVP foundation

This repo delivers **Phase 1 (MVP foundation)**. Below is what comes next, drawn
from the full product roadmap. Nothing here is built yet — it is the honest
"not-done" list plus the intended sequence.

## Phase 1 — MVP foundation ✅ (this repo)
- Auth, catalog, full-text search, cart, checkout, orders
- Pluggable AI assistant (stub → real LLM), content + co-occurrence recommenders
- Dockerized monorepo, migrations, seed catalog, docs

## Phase 2 — Commerce depth
- **Payments:** real gateway integration (tokenized, PCI-aware) replacing the
  simulated cash-on-delivery checkout
- **Shipping:** providers, rates, tracking (`shipments` table)
- **Reviews & ratings**, **wishlist**, **addresses**, **coupons/promotions**
- **Inventory:** movement log (`inventory_log`), low-stock alerts
- **Admin portal:** product/order/customer management, RBAC
- **Order lifecycle:** `order_status_history`, notifications (email/WhatsApp)

## Phase 3 — Intelligence
- **Semantic search:** add a `pgvector` embedding column; hybrid keyword + vector
  ranking (the current `tsvector` search is the fallback tier)
- **Personalized recommendations:** move from heuristic to model-based
  (matrix factorization / neural CF) on `analytics_events`
- **Demand forecasting:** time-series model per SKU for restock/pricing
- **Sentiment analysis** over reviews and support tickets
- **Marketing AI:** segmentation, personalized campaigns, A/B testing

## Phase 4 — Scale & platform
- **Multi-tenant / marketplace:** multiple sellers, commissions
- **Mobile apps** (React Native / Flutter) on the same headless API
- **Omnichannel**, dynamic pricing, autonomous AI agent for ops
- **ERP surface:** accounting, purchasing, POS

## Engineering hardening (ongoing)
- Rate limiting (Redis), audit logs, WAF, MFA for admins
- CI/CD (GitHub Actions), monitoring (Prometheus/Grafana), structured logging
- Test coverage: integration + load tests; contract tests on the API
- Observability for AI: hallucination checks, human-in-the-loop for critical actions

## KPIs to instrument early
Conversion rate, AOV, cart-abandonment, repeat-purchase, assistant usage and
first-contact-resolution, recommendation lift. Add `analytics_events` in Phase 2 to
capture the behavioral data these depend on.
