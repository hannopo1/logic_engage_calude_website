import type {
  Analytics,
  ApproveResult,
  Cart,
  Category,
  ChatResponse,
  Customer,
  Dashboard,
  Offer,
  Order,
  Product,
  ProductAdmin,
  ProductList,
  PurchaseOrder,
  Supplier,
  TimelineStep,
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
  checkoutWith: (shipping_address: string, payment_method = "cod") =>
    fetch(`${API}/orders`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ shipping_address, payment_method }),
    }).then(handle<Order>),
  myOrders: () =>
    fetch(`${API}/orders`, { headers: headers(false) }).then(handle<Order[]>),
  order: (id: number) =>
    fetch(`${API}/orders/${id}`, { headers: headers(false) }).then(handle<Order>),
  orderTimeline: (id: number) =>
    fetch(`${API}/orders/${id}/timeline`, { headers: headers(false) }).then(
      handle<TimelineStep[]>,
    ),

  // Admin (operator) — drop-shipping control room
  adminDashboard: () =>
    fetch(`${API}/admin/dashboard`, { headers: headers(false) }).then(handle<Dashboard>),
  adminPurchaseOrders: (status?: string) =>
    fetch(`${API}/admin/purchase-orders${status ? `?status=${status}` : ""}`, {
      headers: headers(false),
    }).then(handle<PurchaseOrder[]>),
  adminApprove: (id: number) =>
    fetch(`${API}/admin/purchase-orders/${id}/approve`, {
      method: "POST",
      headers: headers(false),
    }).then(handle<ApproveResult & { po: PurchaseOrder }>),
  adminReject: (id: number, note: string, cancel: boolean) =>
    fetch(`${API}/admin/purchase-orders/${id}/reject`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ note, cancel }),
    }).then(handle<PurchaseOrder>),
  adminMarkPurchased: (id: number, supplier_order_ref: string, actual_cost?: string) =>
    fetch(`${API}/admin/purchase-orders/${id}/mark-purchased`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ supplier_order_ref, actual_cost }),
    }).then(handle<PurchaseOrder>),
  adminShip: (id: number, tracking_no: string, carrier?: string) =>
    fetch(`${API}/admin/purchase-orders/${id}/ship`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ tracking_no, carrier }),
    }).then(handle<PurchaseOrder>),
  adminDeliver: (id: number) =>
    fetch(`${API}/admin/purchase-orders/${id}/deliver`, {
      method: "POST",
      headers: headers(false),
    }).then(handle<PurchaseOrder>),
  adminSuppliers: () =>
    fetch(`${API}/admin/suppliers`, { headers: headers(false) }).then(handle<Supplier[]>),

  // Merchant console — products / customers / analytics
  adminProducts: () =>
    fetch(`${API}/admin/products`, { headers: headers(false) }).then(handle<ProductAdmin[]>),
  adminCreateProduct: (body: Record<string, unknown>) =>
    fetch(`${API}/admin/products`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    }).then(handle<ProductAdmin>),
  adminPatchProduct: (id: number, body: Record<string, unknown>) =>
    fetch(`${API}/admin/products/${id}`, {
      method: "PATCH",
      headers: headers(),
      body: JSON.stringify(body),
    }).then(handle<ProductAdmin>),
  adminOffersFor: (productId: number) =>
    fetch(`${API}/admin/offers?product_id=${productId}`, { headers: headers(false) }).then(
      handle<Offer[]>,
    ),
  adminCreateOffer: (body: Record<string, unknown>) =>
    fetch(`${API}/admin/offers`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
    }).then(handle<Offer>),
  adminCustomers: () =>
    fetch(`${API}/admin/customers`, { headers: headers(false) }).then(handle<Customer[]>),
  adminAnalytics: (days = 30) =>
    fetch(`${API}/admin/analytics?days=${days}`, { headers: headers(false) }).then(
      handle<Analytics>,
    ),

  // Public analytics ingest (fire-and-forget)
  track: (body: { event_type: string; path?: string; product_id?: number; query?: string }) =>
    fetch(`${API}/events`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(body),
      keepalive: true,
    }).catch(() => {}),

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
