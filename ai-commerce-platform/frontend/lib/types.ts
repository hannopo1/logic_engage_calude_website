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
