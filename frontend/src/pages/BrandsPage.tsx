import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getBrands } from '@/api/brands';
import { useFilterStore } from '@/store/filterStore';
import { useT } from '@/store/localeStore';
import BrandFilters from '@/components/brand/BrandFilters';
import BrandGrid from '@/components/brand/BrandGrid';
import LoadingSpinner from '@/components/common/LoadingSpinner';

export default function BrandsPage() {
  const [searchParams] = useSearchParams();
  const { search, style_tag, price_range, shipping_tier, page, per_page, setStyleTag } = useFilterStore();
  const t = useT();

  useEffect(() => {
    const styleParam = searchParams.get('style');
    if (styleParam) {
      setStyleTag(styleParam);
    }
  }, [searchParams, setStyleTag]);

  const { data, isLoading, isError } = useQuery({
    queryKey: ['brands', { search, style_tag, price_range, shipping_tier, page, per_page }],
    queryFn: () =>
      getBrands({
        search: search || undefined,
        style_tag: style_tag || undefined,
        price_range: price_range || undefined,
        shipping_tier: shipping_tier || undefined,
        page,
        per_page,
      }),
  });

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-10 lg:py-16">
      <div className="mb-10">
        <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-[0.3em] mb-2">{t('brands.directory')}</p>
        <h1 className="text-3xl lg:text-4xl font-bold text-neutral-900 tracking-tight">{t('brands.allBrands')}</h1>
        {data && (
          <p className="text-sm text-neutral-400 mt-2">
            {t('brands.tracked', { count: data.total, s: data.total !== 1 ? 's' : '' })}
          </p>
        )}
      </div>

      <div className="mb-8">
        <BrandFilters />
      </div>

      {isLoading ? (
        <LoadingSpinner className="py-20" />
      ) : isError ? (
        <div className="text-center py-20">
          <p className="text-neutral-500 text-sm">{t('brands.loadError')}</p>
        </div>
      ) : data ? (
        <>
          <BrandGrid brands={data.data} />
          {data.total > per_page && (
            <div className="flex items-center justify-center gap-2 mt-12">
              {Array.from({ length: Math.ceil(data.total / per_page) }, (_, i) => i + 1).map(
                (pageNum) => (
                  <button
                    key={pageNum}
                    onClick={() => useFilterStore.getState().setPage(pageNum)}
                    className={`w-9 h-9 rounded-md text-sm font-medium transition-colors ${
                      pageNum === page
                        ? 'bg-neutral-900 text-white'
                        : 'text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              )}
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}
