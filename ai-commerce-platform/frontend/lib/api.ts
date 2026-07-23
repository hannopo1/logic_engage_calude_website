import type {
  Cart,
  Category,
  ChatResponse,
  Order,
  Product,
  ProductList,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API = `${BASE}/api/v1`;

/** A stable anonymous session id, so an unauthenticated cart persists. */
function sessionId(): string {
  if (typeof window === "undefined") return "server";
  let sid = localStorage.getItem("sid");
  if (!sid) {
    sid = crypto.randomUUID();
    localStorage.setItem("sid", sid);
  }
  return sid;
}

function token(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

function headers(json = true): Record<string, string> {
  const h: Record<string, string> = {};
  if (json) h["Content-Type"] = "application/json";
  h["X-Session-Id"] = sessionId();
  const t = token();
  if (t) h["Authorization"] = `Bearer ${t}`;
  return h;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Catalog
  products: (params = "") =>
    fetch(`${API}/products${params}`, { cache: "no-store" }).then(handle<ProductList>),
  product: (slug: string) =>
    fetch(`${API}/products/${slug}`, { cache: "no-store" }).then(handle<Product>),
  categories: () =>
    fetch(`${API}/categories`, { cache: "no-store" }).then(handle<Category[]>),
  search: (q: string) =>
    fetch(`${API}/search?q=${encodeURIComponent(q)}`, { cache: "no-store" }).then(
      handle<Product[]>,
    ),
  recommend: (id: number) =>
    fetch(`${API}/ai/recommend/${id}`, { cache: "no-store" }).then(
      handle<{ similar: Product[]; also_bought: Product[] }>,
    ),

  // Cart
  getCart: () => fetch(`${API}/cart`, { headers: headers(false) }).then(handle<Cart>),
  addToCart: (product_id: number, quantity = 1) =>
    fetch(`${API}/cart/items`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ product_id, quantity }),
    }).then(handle<Cart>),
  updateCart: (product_id: number, quantity: number) =>
    fetch(`${API}/cart/items/${product_id}`, {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify({ quantity }),
    }).then(handle<Cart>),
  removeFromCart: (product_id: number) =>
    fetch(`${API}/cart/items/${product_id}`, {
      method: "DELETE",
      headers: headers(false),
    }).then(handle<Cart>),

  // Orders
  checkout: (shipping_address: string) =>
    fetch(`${API}/orders`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ shipping_address }),
    }).then(handle<Order>),

  // Auth
  register: (body: { email: string; password: string; first_name?: string }) =>
    fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle<{ access_token: string }>),
  login: (body: { email: string; password: string }) =>
    fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(handle<{ access_token: string }>),

  // AI
  chat: (message: string, history: { role: string; content: string }[] = []) =>
    fetch(`${API}/ai/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    }).then(handle<ChatResponse>),
};

export function setToken(t: string) {
  localStorage.setItem("token", t);
}
