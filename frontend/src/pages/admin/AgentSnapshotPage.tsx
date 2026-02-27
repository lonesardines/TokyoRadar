import { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Bot, Loader2, Package, Image, DollarSign,
  ShoppingBag, Store, Tag, AlertCircle,
} from 'lucide-react';
import { getAgentJob, getAgentSnapshot } from '@/api/agent';
import ProductCard from '@/components/brand/ProductCard';
import type { SnapshotMetrics, Item } from '@/types';

function MetricCard({ icon: Icon, label, value, sub }: {
  icon: typeof Package;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-neutral-200 p-3">
      <div className="flex items-center gap-2 text-neutral-400 mb-1">
        <Icon size={12} />
        <span className="text-[10px] uppercase tracking-wider font-medium">{label}</span>
      </div>
      <div className="text-lg font-semibold text-neutral-900">{value}</div>
      {sub && <div className="text-xs text-neutral-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function MetricsBar({ metrics }: { metrics: SnapshotMetrics }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      <MetricCard icon={Package} label="Items" value={String(metrics.items_total)} />
      <MetricCard
        icon={Image}
        label="With Images"
        value={String(metrics.items_with_images)}
        sub={metrics.items_total > 0 ? `${Math.round(metrics.items_with_images / metrics.items_total * 100)}%` : undefined}
      />
      <MetricCard
        icon={DollarSign}
        label="With Prices"
        value={String(metrics.items_with_prices)}
      />
      <MetricCard icon={ShoppingBag} label="In Stock" value={String(metrics.items_in_stock)} />
      <MetricCard
        icon={Store}
        label="Listings"
        value={String(metrics.listings_total)}
        sub={`${metrics.channels_count} channels`}
      />
      <MetricCard
        icon={Tag}
        label="Avg Price"
        value={metrics.avg_price_usd != null ? `$${metrics.avg_price_usd.toFixed(0)}` : '--'}
        sub={metrics.price_range_usd ? `$${metrics.price_range_usd[0].toFixed(0)}-$${metrics.price_range_usd[1].toFixed(0)}` : undefined}
      />
    </div>
  );
}

export default function AgentSnapshotPage() {
  const { id } = useParams<{ id: string }>();
  const jobId = Number(id);
  const [typeFilter, setTypeFilter] = useState('');
  const [stockFilter, setStockFilter] = useState<'all' | 'in_stock' | 'out_of_stock'>('all');

  const { data: job } = useQuery({
    queryKey: ['agent-job', jobId],
    queryFn: () => getAgentJob(jobId),
  });

  const { data: snapshot, isLoading } = useQuery({
    queryKey: ['agent-snapshot', jobId],
    queryFn: () => getAgentSnapshot(jobId),
  });

  const items = snapshot?.items ?? [];
  const metrics = snapshot?.metrics;

  // Get unique item types for filter dropdown
  const itemTypes = useMemo(() => {
    const types = new Set<string>();
    for (const item of items) {
      if (item.item_type) types.add(item.item_type);
    }
    return Array.from(types).sort();
  }, [items]);

  // Apply filters
  const filteredItems = useMemo(() => {
    let result = items;
    if (typeFilter) {
      result = result.filter(i => i.item_type === typeFilter);
    }
    if (stockFilter === 'in_stock') {
      result = result.filter(i => i.in_stock === true);
    } else if (stockFilter === 'out_of_stock') {
      result = result.filter(i => i.in_stock === false);
    }
    return result;
  }, [items, typeFilter, stockFilter]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 size={24} className="animate-spin text-neutral-400" />
      </div>
    );
  }

  return (
    <div>
      <Link
        to={`/admin/agent/${jobId}`}
        className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 mb-4"
      >
        <ArrowLeft size={14} />
        Back to Session
      </Link>

      {/* Job Info Card */}
      {job && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 mb-6">
          <div className="flex items-center gap-3">
            <Bot size={18} className="text-neutral-500" />
            <div>
              <h1 className="text-lg font-bold text-neutral-900">
                Job #{job.id} Products — {job.brand_slug}
              </h1>
              <div className="flex items-center gap-3 mt-1 text-sm text-neutral-500">
                <span>{job.model}</span>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full ${
                  job.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-neutral-100 text-neutral-600'
                }`}>
                  {job.status}
                </span>
                {job.total_cost_usd != null && <span>${job.total_cost_usd.toFixed(4)}</span>}
                {job.completed_at && <span>{new Date(job.completed_at).toLocaleString()}</span>}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Metrics */}
      {metrics && <MetricsBar metrics={metrics} />}

      {/* No snapshot fallback */}
      {!metrics && items.length === 0 && (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center mb-6">
          <AlertCircle size={32} className="mx-auto text-neutral-300 mb-3" />
          <p className="text-neutral-500 font-medium">No snapshot data</p>
          <p className="text-sm text-neutral-400 mt-1">
            This run was before the snapshot feature or produced no items.
          </p>
        </div>
      )}

      {/* Filters */}
      {items.length > 0 && (
        <div className="flex items-center gap-3 mb-4">
          <span className="text-sm text-neutral-500">
            {filteredItems.length} of {items.length} items
          </span>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            <option value="">All Types</option>
            {itemTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <select
            value={stockFilter}
            onChange={(e) => setStockFilter(e.target.value as 'all' | 'in_stock' | 'out_of_stock')}
            className="px-3 py-1.5 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          >
            <option value="all">All Stock</option>
            <option value="in_stock">In Stock</option>
            <option value="out_of_stock">Out of Stock</option>
          </select>
        </div>
      )}

      {/* Product Grid */}
      {filteredItems.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {filteredItems.map((item) => (
            <ProductCard key={item.id} item={item as Item} />
          ))}
        </div>
      )}

      {/* Tool Summary */}
      {snapshot?.tool_summary && (
        <div className="mt-8">
          <details>
            <summary className="text-sm font-medium text-neutral-500 cursor-pointer hover:text-neutral-700">
              Tool Summary
            </summary>
            <div className="mt-2 bg-white rounded-lg border border-neutral-200 p-4 text-xs space-y-3">
              <div>
                <span className="font-medium text-neutral-600">Total tool calls:</span>{' '}
                {snapshot.tool_summary.total_tool_calls}
              </div>
              {Object.keys(snapshot.tool_summary.tools_used).length > 0 && (
                <div>
                  <span className="font-medium text-neutral-600">Tools used:</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {Object.entries(snapshot.tool_summary.tools_used).map(([name, count]) => (
                      <span key={name} className="px-2 py-0.5 bg-neutral-100 rounded text-neutral-600">
                        {name}: {count}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {Object.keys(snapshot.tool_summary.scrape_results).length > 0 && (
                <div>
                  <span className="font-medium text-neutral-600">Scrape results:</span>
                  <div className="mt-1 space-y-1">
                    {Object.entries(snapshot.tool_summary.scrape_results).map(([domain, info]) => (
                      <div key={domain} className="text-neutral-500">
                        {domain}: {info.products_found} products
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {snapshot.tool_summary.errors.length > 0 && (
                <div>
                  <span className="font-medium text-red-600">Errors:</span>
                  <div className="mt-1 space-y-1">
                    {snapshot.tool_summary.errors.map((err, i) => (
                      <div key={i} className="text-red-500">{err}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
