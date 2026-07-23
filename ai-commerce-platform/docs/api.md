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
