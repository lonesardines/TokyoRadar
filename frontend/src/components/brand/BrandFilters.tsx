import { Search, X } from 'lucide-react';
import { useFilterStore } from '@/store/filterStore';
import StyleTag from '@/components/common/StyleTag';
import { cn } from '@/lib/utils';

const STYLE_TAGS = [
  'streetwear',
  'avant-garde',
  'workwear',
  'outdoor',
  'denim',
  'luxury',
  'casual',
  'select-shop',
];

const PRICE_RANGES = [
  { value: '', label: 'All' },
  { value: 'budget', label: '$' },
  { value: 'low_mid', label: '$$' },
  { value: 'mid', label: '$$$' },
  { value: 'mid_high', label: '$$$$' },
  { value: 'high', label: '$$$$$' },
];

const SHIPPING_TIERS = [
  { value: '', label: 'All' },
  { value: 'green', label: 'Green', color: 'bg-shipping-green' },
  { value: 'yellow', label: 'Yellow', color: 'bg-shipping-yellow' },
  { value: 'red', label: 'Red', color: 'bg-shipping-red' },
];

export default function BrandFilters() {
  const { search, style_tag, price_range, shipping_tier, setSearch, setStyleTag, setPriceRange, setShippingTier, reset } =
    useFilterStore();

  const hasActiveFilters = search || style_tag || price_range || shipping_tier;

  return (
    <div className="space-y-5">
      <div className="relative">
        <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search brands..."
          className="w-full pl-11 pr-4 py-3 border border-neutral-200 rounded-lg text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-neutral-400 focus:ring-1 focus:ring-neutral-200 transition-colors bg-white"
        />
      </div>

      <div className="space-y-3">
        <div>
          <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest mb-2 block">Style</span>
          <div className="flex flex-wrap gap-1.5">
            {STYLE_TAGS.map((tag) => (
              <StyleTag
                key={tag}
                tag={tag}
                active={style_tag === tag}
                onClick={() => setStyleTag(style_tag === tag ? '' : tag)}
              />
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-6">
          <div>
            <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest mb-2 block">Price</span>
            <div className="flex gap-1">
              {PRICE_RANGES.map((range) => (
                <button
                  key={range.value}
                  onClick={() => setPriceRange(price_range === range.value ? '' : range.value)}
                  className={cn(
                    'px-3 py-1.5 text-xs font-medium rounded-md border transition-all',
                    price_range === range.value
                      ? 'border-neutral-900 bg-neutral-900 text-white'
                      : 'border-neutral-200 text-neutral-500 hover:border-neutral-400 hover:text-neutral-700'
                  )}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest mb-2 block">Shipping</span>
            <div className="flex gap-1">
              {SHIPPING_TIERS.map((tier) => (
                <button
                  key={tier.value}
                  onClick={() => setShippingTier(shipping_tier === tier.value ? '' : tier.value)}
                  className={cn(
                    'px-3 py-1.5 text-xs font-medium rounded-md border transition-all inline-flex items-center gap-1.5',
                    shipping_tier === tier.value
                      ? 'border-neutral-900 bg-neutral-900 text-white'
                      : 'border-neutral-200 text-neutral-500 hover:border-neutral-400 hover:text-neutral-700'
                  )}
                >
                  {tier.color && (
                    <span className={cn('h-2 w-2 rounded-full', tier.color)} />
                  )}
                  {tier.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {hasActiveFilters && (
        <button
          onClick={reset}
          className="inline-flex items-center gap-1.5 text-xs text-neutral-500 hover:text-neutral-900 transition-colors"
        >
          <X size={14} />
          Clear all filters
        </button>
      )}
    </div>
  );
}
