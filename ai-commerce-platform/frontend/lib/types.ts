export interface Product {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  price: string;
  sku?: string | null;
  stock_qty: number;
  image?: string | null;
  tags?: string | null;
  category_id?: number | null;
  seo_title?: string | null;
}

export interface ProductList {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  parent_id?: number | null;
}

export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
  line_total: string;
}

export interface Cart {
  id: number;
  items: CartItem[];
  subtotal: string;
  item_count: number;
}

export interface Order {
  id: number;
  status: string;
  payment_method?: string;
  payment_status: string;
  total_amount: string;
  shipping_address?: string | null;
  created_at: string;
  items: {
    product_id: number | null;
    product_name: string;
    quantity: number;
    unit_price: string;
    total_price: string;
  }[];
}

export interface ChatResponse {
  reply: string;
  provider: string;
  products: Product[];
}

// ---------- Drop-shipping / fulfillment ----------

export interface TimelineStep {
  status: string;
  label: string;
  at?: string | null;
  done: boolean;
}

export interface POEvent {
  status: string;
  note?: string | null;
  actor: string;
  created_at: string;
}

export interface PurchaseOrder {
  id: number;
  order_id: number;
  order_item_id: number;
  supplier_offer_id?: number | null;
  status: string;
  quantity: number;
  expected_cost?: string | null;
  actual_cost?: string | null;
  supplier_order_ref?: string | null;
  tracking_no?: string | null;
  carrier?: string | null;
  created_at: string;
  product_name?: string | null;
  supplier_name?: string | null;
  supplier_url?: string | null;
  customer_address?: string | null;
  selling_total?: string | null;
  events: POEvent[];
}

export interface Supplier {
  id: number;
  name: string;
  slug: string;
  kind: string;
  region: string;
  mode: string;
  website?: string | null;
  notes?: string | null;
  is_active: boolean;
}

export interface Dashboard {
  po_counts: Record<string, number>;
  orders_today: number;
  revenue_total: string;
  expected_cost_open: string;
  estimated_margin_percent?: number | null;
}

export interface PurchasePackage {
  purchase_order_id: number;
  supplier?: string | null;
  product_url?: string | null;
  quantity: number;
  max_unit_price?: string | null;
  expected_total_cost?: string | null;
  currency: string;
  ship_to_address?: string | null;
  instructions: string;
}

export interface ApproveResult {
  mode: string;
  result: string;
  package: PurchasePackage;
}

// ---------- Merchant console ----------

export interface ProductAdmin {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  price: string;
  cost_price?: string | null;
  sku?: string | null;
  stock_qty: number;
  image?: string | null;
  tags?: string | null;
  category_id?: number | null;
  fulfillment_type: string; // dropship | own_stock
  is_active: boolean;
  offer_count: number;
}

export interface Offer {
  id: number;
  product_id: number;
  supplier_id: number;
  url?: string | null;
  external_sku?: string | null;
  supplier_price: string;
  shipping_cost: string;
  currency: string;
  lead_time_days: number;
  is_active: boolean;
}

export interface Customer {
  id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  created_at: string;
  order_count: number;
  total_spent: string;
}

export interface Analytics {
  days: number;
  unique_visitors: number;
  page_views: number;
  product_views: number;
  searches: number;
  add_to_cart: number;
  orders: number;
  conversion_rate: number;
  funnel: { key: string; label: string; count: number }[];
  top_products: { label: string; count: number }[];
  top_searches: { label: string; count: number }[];
  daily_visitors: { label: string; count: number }[];
}
