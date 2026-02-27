import { useState, useMemo } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Loader2, TrendingUp, TrendingDown, Minus,
  Package, Image, DollarSign, ShoppingBag, Store, Tag,
} from 'lucide-react';
import { compareAgentJobs, getAgentSnapshot } from '@/api/agent';
import ProductCard from '@/components/brand/ProductCard';
import type { CompareResponse, CompareDeltas, Item } from '@/types';

type TabKey = 'all_a' | 'all_b' | 'only_a' | 'only_b' | 'price_changes';

function DeltaCard({ icon: Icon, label, valueA, valueB, delta, format = 'number' }: {
  icon: typeof Package;
  label: string;
  valueA: number | null | undefined;
  valueB: number | null | undefined;
  delta: number | null | undefined;
  format?: 'number' | 'currency';
}) {
  const fmt = (v: number | null | undefined) => {
    if (v == null) return '--';
    return format === 'currency' ? `$${v.toFixed(2)}` : String(v);
  };

  let deltaColor = 'text-neutral-400';
  let DeltaIcon = Minus;
  let deltaText = '--';

  if (delta != null && delta !== 0) {
    // For cost, lower is better; for everything else, higher is better
    const isPositive = label === 'Cost' ? delta < 0 : delta > 0;
    deltaColor = isPositive ? 'text-green-600' : 'text-red-500';
    DeltaIcon = isPositive ? TrendingUp : TrendingDown;
    const sign = delta > 0 ? '+' : '';
    deltaText = format === 'currency' ? `${sign}$${delta.toFixed(2)}` : `${sign}${delta}`;
  } else if (delta === 0) {
    deltaText = '0';
  }

  return (
    <div className="bg-white rounded-lg border border-neutral-200 p-3">
      <div className="flex items-center gap-2 text-neutral-400 mb-1">
        <Icon size={12} />
        <span className="text-[10px] uppercase tracking-wider font-medium">{label}</span>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-sm text-neutral-400">{fmt(valueA)}</span>
        <span className="text-neutral-300">&rarr;</span>
        <span className="text-sm font-semibold text-neutral-900">{fmt(valueB)}</span>
      </div>
      <div className={`flex items-center gap-1 mt-1 text-xs font-medium ${deltaColor}`}>
        <DeltaIcon size={12} />
        {deltaText}
      </div>
    </div>
  );
}

function JobHeader({ job, label }: { job: CompareResponse['job_a']; label: string }) {
  return (
    <div className="flex-1 bg-white rounded-lg border border-neutral-200 p-3">
      <div className="text-xs text-neutral-400 uppercase tracking-wider mb-1">{label}</div>
      <div className="font-semibold text-neutral-900">
        Job #{job.id} — {job.brand_slug}
      </div>
      <div className="flex items-center gap-3 mt-1 text-xs text-neutral-500">
        <span>{job.model}</span>
        {job.completed_at && <span>{new Date(job.completed_at).toLocaleString()}</span>}
        {job.cost_usd != null && <span>${job.cost_usd.toFixed(4)}</span>}
      </div>
    </div>
  );
}

export default function AgentComparePage() {
  const [searchParams] = useSearchParams();
  const jobA = Number(searchParams.get('a'));
  const jobB = Number(searchParams.get('b'));
  const [activeTab, setActiveTab] = useState<TabKey>('all_a');

  const { data: compare, isLoading: compareLoading } = useQuery({
    queryKey: ['agent-compare', jobA, jobB],
    queryFn: () => compareAgentJobs(jobA, jobB),
    enabled: jobA > 0 && jobB > 0,
  });

  const { data: snapA } = useQuery({
    queryKey: ['agent-snapshot', jobA],
    queryFn: () => getAgentSnapshot(jobA),
    enabled: jobA > 0,
  });

  const { data: snapB } = useQuery({
    queryKey: ['agent-snapshot', jobB],
    queryFn: () => getAgentSnapshot(jobB),
    enabled: jobB > 0,
  });

  const itemsA = snapA?.items ?? [];
  const itemsB = snapB?.items ?? [];
  const diff = compare?.item_diff;

  // Items filtered by tab
  const displayItems = useMemo(() => {
    if (!diff) return { left: itemsA, right: itemsB };

    const onlyASet = new Set(diff.only_in_a);
    const onlyBSet = new Set(diff.only_in_b);
    const priceNameSet = new Set(diff.price_changes.map(p => p.name));

    switch (activeTab) {
      case 'only_a':
        return {
          left: itemsA.filter(i => onlyASet.has(i.name_en)),
          right: [],
        };
      case 'only_b':
        return {
          left: [],
          right: itemsB.filter(i => onlyBSet.has(i.name_en)),
        };
      case 'price_changes':
        return {
          left: itemsA.filter(i => priceNameSet.has(i.name_en)),
          right: itemsB.filter(i => priceNameSet.has(i.name_en)),
        };
      case 'all_b':
        return { left: [], right: itemsB };
      case 'all_a':
      default:
        return { left: itemsA, right: [] };
    }
  }, [activeTab, itemsA, itemsB, diff]);

  if (!jobA || !jobB) {
    return (
      <div className="text-center py-20">
        <p className="text-neutral-400">Select two jobs to compare.</p>
        <Link to="/admin/agent" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
          Back to Agent Jobs
        </Link>
      </div>
    );
  }

  if (compareLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 size={24} className="animate-spin text-neutral-400" />
      </div>
    );
  }

  if (!compare) {
    return (
      <div className="text-center py-20">
        <p className="text-neutral-400">Failed to load comparison data.</p>
      </div>
    );
  }

  const d = compare.deltas;
  const ma = compare.job_a.metrics;
  const mb = compare.job_b.metrics;

  const tabs: { key: TabKey; label: string; count?: number }[] = [
    { key: 'all_a', label: `All A`, count: itemsA.length },
    { key: 'all_b', label: `All B`, count: itemsB.length },
    { key: 'only_a', label: 'Only in A', count: diff?.only_in_a.length },
    { key: 'only_b', label: 'Only in B', count: diff?.only_in_b.length },
    { key: 'price_changes', label: 'Price Changes', count: diff?.price_changes.length },
  ];

  return (
    <div>
      <Link
        to="/admin/agent"
        className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 mb-4"
      >
        <ArrowLeft size={14} />
        Back to Agent Jobs
      </Link>

      {/* Job headers side by side */}
      <div className="flex gap-3 mb-6">
        <JobHeader job={compare.job_a} label="Job A" />
        <JobHeader job={compare.job_b} label="Job B" />
      </div>

      {/* Delta metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3 mb-6">
        <DeltaCard icon={Package} label="Items" valueA={ma?.items_total} valueB={mb?.items_total} delta={d.items_total} />
        <DeltaCard icon={Image} label="Images" valueA={ma?.items_with_images} valueB={mb?.items_with_images} delta={d.items_with_images} />
        <DeltaCard icon={DollarSign} label="Prices" valueA={ma?.items_with_prices} valueB={mb?.items_with_prices} delta={d.items_with_prices} />
        <DeltaCard icon={ShoppingBag} label="In Stock" valueA={ma?.items_in_stock} valueB={mb?.items_in_stock} delta={d.items_in_stock} />
        <DeltaCard icon={Store} label="Listings" valueA={ma?.listings_total} valueB={mb?.listings_total} delta={d.listings_total} />
        <DeltaCard icon={Store} label="Channels" valueA={ma?.channels_count} valueB={mb?.channels_count} delta={d.channels_count} />
        <DeltaCard icon={Tag} label="Avg Price" valueA={ma?.avg_price_usd} valueB={mb?.avg_price_usd} delta={d.avg_price_usd} format="currency" />
      </div>

      {/* Item diff summary */}
      {diff && (
        <div className="bg-white rounded-lg border border-neutral-200 p-4 mb-6">
          <h3 className="text-sm font-medium text-neutral-700 mb-3">Item Diff Summary</h3>
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-red-100 border border-red-300" />
              <span className="text-neutral-600">Only in A: <strong>{diff.only_in_a.length}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-green-100 border border-green-300" />
              <span className="text-neutral-600">Only in B: <strong>{diff.only_in_b.length}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-neutral-100 border border-neutral-300" />
              <span className="text-neutral-600">In Both: <strong>{diff.in_both}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded bg-yellow-100 border border-yellow-300" />
              <span className="text-neutral-600">Price Changes: <strong>{diff.price_changes.length}</strong></span>
            </div>
          </div>

          {/* Price changes table */}
          {diff.price_changes.length > 0 && (
            <div className="mt-4 overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-neutral-100">
                    <th className="text-left py-1.5 pr-4 text-neutral-500 font-medium">Item</th>
                    <th className="text-right py-1.5 px-3 text-neutral-500 font-medium">A Price</th>
                    <th className="text-right py-1.5 px-3 text-neutral-500 font-medium">B Price</th>
                    <th className="text-right py-1.5 pl-3 text-neutral-500 font-medium">Diff</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-50">
                  {diff.price_changes.slice(0, 20).map((pc) => {
                    const priceDiff = pc.b_price - pc.a_price;
                    return (
                      <tr key={pc.name}>
                        <td className="py-1.5 pr-4 text-neutral-700 truncate max-w-[200px]">{pc.name}</td>
                        <td className="py-1.5 px-3 text-right text-neutral-500">${pc.a_price.toFixed(2)}</td>
                        <td className="py-1.5 px-3 text-right text-neutral-700 font-medium">${pc.b_price.toFixed(2)}</td>
                        <td className={`py-1.5 pl-3 text-right font-medium ${priceDiff < 0 ? 'text-green-600' : priceDiff > 0 ? 'text-red-500' : 'text-neutral-400'}`}>
                          {priceDiff > 0 ? '+' : ''}{priceDiff.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {diff.price_changes.length > 20 && (
                <p className="text-xs text-neutral-400 mt-2">
                  Showing 20 of {diff.price_changes.length} price changes
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab navigation */}
      <div className="flex items-center gap-1 mb-4 border-b border-neutral-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-neutral-900 text-neutral-900'
                : 'border-transparent text-neutral-400 hover:text-neutral-600'
            }`}
          >
            {tab.label}
            {tab.count != null && (
              <span className="ml-1.5 text-xs text-neutral-400">({tab.count})</span>
            )}
          </button>
        ))}
      </div>

      {/* Product grids based on active tab */}
      {activeTab === 'price_changes' ? (
        /* Side by side for price changes */
        <div className="grid grid-cols-2 gap-6">
          <div>
            <h3 className="text-sm font-medium text-neutral-500 mb-3">Job A</h3>
            <div className="grid grid-cols-2 gap-3">
              {displayItems.left.map((item) => (
                <ProductCard key={item.id} item={item as Item} />
              ))}
            </div>
            {displayItems.left.length === 0 && (
              <p className="text-sm text-neutral-400 text-center py-8">No items</p>
            )}
          </div>
          <div>
            <h3 className="text-sm font-medium text-neutral-500 mb-3">Job B</h3>
            <div className="grid grid-cols-2 gap-3">
              {displayItems.right.map((item) => (
                <ProductCard key={item.id} item={item as Item} />
              ))}
            </div>
            {displayItems.right.length === 0 && (
              <p className="text-sm text-neutral-400 text-center py-8">No items</p>
            )}
          </div>
        </div>
      ) : (
        /* Single grid for all/only tabs */
        <div>
          {(displayItems.left.length > 0 || displayItems.right.length > 0) ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {[...displayItems.left, ...displayItems.right].map((item) => (
                <ProductCard key={item.id} item={item as Item} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-neutral-400 text-center py-12">No items in this view</p>
          )}
        </div>
      )}
    </div>
  );
}
