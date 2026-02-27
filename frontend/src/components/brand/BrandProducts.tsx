import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getItems } from '@/api/items';
import { useT } from '@/store/localeStore';
import ProductCard from './ProductCard';
import LoadingSpinner from '@/components/common/LoadingSpinner';

interface BrandProductsProps {
  slug: string;
}

const PER_PAGE = 12;

export default function BrandProducts({ slug }: BrandProductsProps) {
  const t = useT();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState('');
  const [seasonFilter, setSeasonFilter] = useState('');
  const [inStockOnly, setInStockOnly] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['items', slug, page, typeFilter, seasonFilter, inStockOnly],
    queryFn: () =>
      getItems({
        brand_slug: slug,
        page,
        per_page: PER_PAGE,
        item_type: typeFilter || undefined,
        season_code: seasonFilter || undefined,
        in_stock: inStockOnly || undefined,
      }),
  });

  // Fetch all items once (no filters) to extract filter options
  const { data: allData } = useQuery({
    queryKey: ['items', slug, 'all-meta'],
    queryFn: () => getItems({ brand_slug: slug, per_page: 1 }),
  });

  // Fetch unfiltered items to derive filter options (API max per_page is 100)
  const { data: filterData } = useQuery({
    queryKey: ['items', slug, 'filter-options'],
    queryFn: () => getItems({ brand_slug: slug, per_page: 100 }),
    enabled: (allData?.total ?? 0) > 0,
  });

  const { itemTypes, seasonCodes } = useMemo(() => {
    const items = filterData?.data ?? [];
    const types = new Set<string>();
    const seasons = new Set<string>();
    for (const item of items) {
      if (item.item_type) types.add(item.item_type);
      if (item.season_code) seasons.add(item.season_code);
    }
    return {
      itemTypes: Array.from(types).sort(),
      seasonCodes: Array.from(seasons).sort(),
    };
  }, [filterData]);

  // Don't render section at all if brand has no items
  if (!isLoading && allData && allData.total === 0) return null;

  const totalPages = data ? Math.ceil(data.total / PER_PAGE) : 0;

  const resetFilters = () => {
    setPage(1);
    setTypeFilter('');
    setSeasonFilter('');
    setInStockOnly(false);
  };

  const handleFilterChange = (setter: (v: string) => void) => (v: string) => {
    setPage(1);
    setter(v);
  };

  return (
    <div className="mb-10">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-neutral-900 tracking-tight">
          {t('brand.products')}
        </h2>
        {data && (
          <p className="text-sm text-neutral-400 mt-1">
            {t('brand.productsCount', { count: data.total })}
          </p>
        )}
      </div>

      {/* Filter bar */}
      {(itemTypes.length > 0 || seasonCodes.length > 0) && (
        <div className="flex flex-wrap items-center gap-3 mb-6">
          {itemTypes.length > 0 && (
            <select
              value={typeFilter}
              onChange={(e) => handleFilterChange(setTypeFilter)(e.target.value)}
              className="text-sm border border-neutral-200 rounded-lg px-3 py-1.5 text-neutral-700 bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
            >
              <option value="">{t('brand.allTypes')}</option>
              {itemTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          )}

          {seasonCodes.length > 0 && (
            <select
              value={seasonFilter}
              onChange={(e) => handleFilterChange(setSeasonFilter)(e.target.value)}
              className="text-sm border border-neutral-200 rounded-lg px-3 py-1.5 text-neutral-700 bg-white focus:outline-none focus:ring-1 focus:ring-neutral-300"
            >
              <option value="">{t('brand.allSeasons')}</option>
              {seasonCodes.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </select>
          )}

          <label className="inline-flex items-center gap-2 text-sm text-neutral-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(e) => {
                setPage(1);
                setInStockOnly(e.target.checked);
              }}
              className="rounded border-neutral-300 text-neutral-900 focus:ring-neutral-300"
            />
            {t('brand.inStockOnly')}
          </label>

          {(typeFilter || seasonFilter || inStockOnly) && (
            <button
              onClick={resetFilters}
              className="text-xs text-neutral-400 hover:text-neutral-700 transition-colors"
            >
              {t('filters.clearAll')}
            </button>
          )}
        </div>
      )}

      {/* Grid */}
      {isLoading ? (
        <LoadingSpinner className="py-16" />
      ) : data && data.data.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {data.data.map((item) => (
            <ProductCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <div className="py-16 text-center">
          <p className="text-sm text-neutral-400">{t('brand.noProducts')}</p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-neutral-200 rounded-lg text-neutral-600 hover:border-neutral-400 hover:text-neutral-900 transition-colors disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft size={14} />
            Prev
          </button>
          <span className="text-sm text-neutral-500">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-sm border border-neutral-200 rounded-lg text-neutral-600 hover:border-neutral-400 hover:text-neutral-900 transition-colors disabled:opacity-30 disabled:pointer-events-none"
          >
            Next
            <ChevronRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
}
