export interface Brand {
  id: number;
  slug: string;
  name_en: string;
  name_ja: string | null;
  designer: string | null;
  founded_year: number | null;
  headquarters: string | null;
  website_jp: string | null;
  website_us: string | null;
  has_redirect: boolean;
  style_tags: string[];
  price_range: 'budget' | 'mid' | 'mid_high' | 'high' | 'luxury';
  description_en: string | null;
  description_ja: string | null;
  shipping_tier: 'green' | 'yellow' | 'red';
  buy_guide: BuyGuide | null;
  logo_url: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface BuyGuide {
  summary: string;
  best_channels: BuyChannel[];
}

export interface BuyChannel {
  url: string;
  name: string;
  tier: 'green' | 'yellow' | 'red';
  notes: string;
}

export interface Retailer {
  id: number;
  slug: string;
  name: string;
  website: string;
  country: string;
  ships_to_us: boolean;
  shipping_tier: 'green' | 'yellow' | 'red';
  supported_proxies: string[];
  payment_methods: string[];
  description_en: string | null;
  logo_url: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface ProxyService {
  id: number;
  slug: string;
  name: string;
  website: string;
  service_type: 'proxy' | 'forwarding' | 'both';
  fee_structure: Record<string, unknown>;
  supported_retailers: string[];
  shipping_methods: string[];
  avg_delivery_days_us: number;
  pros: string[];
  cons: string[];
  description_en: string | null;
  logo_url: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  parent_id: number | null;
  sort_order: number;
  children?: Category[] | null;
}
