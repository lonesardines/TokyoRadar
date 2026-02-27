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

export interface PriceListing {
  id: number;
  retailer_slug: string;
  retailer_name: string;
  price_jpy: number | null;
  price_usd: number | null;
  in_stock: boolean;
  available_sizes: string[] | null;
  url: string | null;
  last_checked_at: string | null;
}

// Phase 2: Items + ScrapeJobs

export interface Item {
  id: number;
  brand_id: number;
  collection_id: number | null;
  name_en: string;
  name_ja: string | null;
  item_type: string | null;
  price_jpy: number | null;
  price_usd: number | null;
  compare_at_price_usd: number | null;
  material: string | null;
  sizes: string[] | null;
  primary_image_url: string | null;
  source_url: string | null;
  external_id: string | null;
  handle: string | null;
  vendor: string | null;
  product_type_raw: string | null;
  tags: string[] | null;
  colors: string[] | null;
  season_code: string | null;
  sku: string | null;
  in_stock: boolean | null;
  price_listings: PriceListing[];
  created_at: string;
  updated_at: string | null;
}

export interface ItemDetail extends Item {
  body_html_raw: string | null;
  shopify_data: Record<string, unknown> | null;
}

export interface ScrapeJob {
  id: number;
  brand_id: number;
  source: string;
  status: 'pending' | 'scraping' | 'validating' | 'storing' | 'completed' | 'failed';
  celery_task_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  items_found: number | null;
  items_stored: number | null;
  items_flagged: number | null;
  errors: Record<string, unknown> | null;
  flags: ValidationFlagGroup[] | null;
  config: Record<string, unknown> | null;
  created_at: string;
}

export interface ValidationFlagGroup {
  external_id: string;
  name: string;
  flags: ValidationFlag[];
}

export interface ValidationFlag {
  field: string;
  severity: 'warning' | 'error';
  message: string;
}

// Agent Jobs

export interface AgentJob {
  id: number;
  brand_slug: string;
  model: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  celery_task_id?: string;
  started_at?: string;
  completed_at?: string;
  tool_calls?: number;
  total_input_tokens?: number;
  total_output_tokens?: number;
  total_cost_usd?: number;
  has_snapshot?: boolean;
  session_file?: string;
  result?: Record<string, unknown>;
  errors?: Record<string, unknown>;
  created_at: string;
}

// Agent Snapshot & Compare types

export interface SnapshotMetrics {
  items_total: number;
  items_with_images: number;
  items_with_prices: number;
  items_in_stock: number;
  listings_total: number;
  listings_with_urls: number;
  channels: string[];
  channels_count: number;
  price_range_usd: [number, number] | null;
  avg_price_usd: number | null;
}

export interface ToolSummary {
  total_tool_calls: number;
  tools_used: Record<string, number>;
  scrape_results: Record<string, { products_found: number; source_url: string }>;
  errors: string[];
}

export interface SnapshotResponse {
  items: Item[];
  metrics: SnapshotMetrics | null;
  tool_summary: ToolSummary | null;
}

export interface CompareJobSummary {
  id: number;
  brand_slug: string;
  model: string;
  completed_at: string | null;
  cost_usd: number | null;
  metrics: SnapshotMetrics | null;
}

export interface CompareDeltas {
  items_total: number | null;
  items_with_images: number | null;
  items_with_prices: number | null;
  items_in_stock: number | null;
  listings_total: number | null;
  listings_with_urls: number | null;
  channels_count: number | null;
  avg_price_usd: number | null;
  cost_usd: number | null;
}

export interface ItemDiff {
  only_in_a: string[];
  only_in_b: string[];
  in_both: number;
  price_changes: Array<{ name: string; a_price: number; b_price: number }>;
}

export interface CompareResponse {
  job_a: CompareJobSummary;
  job_b: CompareJobSummary;
  deltas: CompareDeltas;
  item_diff: ItemDiff;
}

export interface SessionEntry {
  type: 'api_call' | 'tool_exec';
  timestamp?: string;
  // api_call fields
  model?: string;
  usage?: { prompt_tokens?: number; completion_tokens?: number };
  latency_ms?: number;
  cost_usd?: number;
  finish_reason?: string;
  content?: string;
  tool_calls?: Array<{ id?: string; name?: string; arguments?: string }>;
  request_messages?: Array<{ role: string; content?: string; tool_call_id?: string }>;
  cumulative_input_tokens?: number;
  cumulative_output_tokens?: number;
  cumulative_cost_usd?: number;
  // tool_exec fields
  name?: string;
  input?: Record<string, unknown> | string;
  output?: Record<string, unknown> | string;
  duration_ms?: number;
}

export interface SessionSummary {
  total_entries: number;
  api_calls: number;
  tool_execs: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  total_latency_ms: number;
  total_tool_duration_ms: number;
  avg_latency_ms: number;
}

export interface SessionData {
  entries: SessionEntry[];
  summary: SessionSummary;
}
