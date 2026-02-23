import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { getBrand } from '@/api/brands';
import { useT } from '@/store/localeStore';
import ShippingBadge from '@/components/common/ShippingBadge';
import PriceRangeBadge from '@/components/common/PriceRangeBadge';
import StyleTag from '@/components/common/StyleTag';
import BuyGuideCard from '@/components/brand/BuyGuideCard';
import LoadingSpinner from '@/components/common/LoadingSpinner';

export default function BrandDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const t = useT();

  const { data: brand, isLoading, isError } = useQuery({
    queryKey: ['brand', slug],
    queryFn: () => getBrand(slug!),
    enabled: !!slug,
  });

  if (isLoading) {
    return <LoadingSpinner className="py-32" size="lg" />;
  }

  if (isError || !brand) {
    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 text-center">
        <p className="text-neutral-500 text-sm">{t('brand.notFound')}</p>
        <Link to="/brands" className="text-sm text-neutral-400 hover:text-neutral-900 mt-4 inline-block transition-colors">
          {t('brand.backToBrands')}
        </Link>
      </div>
    );
  }

  const infoItems = [
    brand.designer && { label: t('brand.designer'), value: brand.designer },
    brand.founded_year && { label: t('brand.founded'), value: String(brand.founded_year) },
    brand.headquarters && { label: t('brand.hq'), value: brand.headquarters },
  ].filter(Boolean) as { label: string; value: string }[];

  return (
    <div className="max-w-4xl mx-auto px-6 lg:px-8 py-10 lg:py-16">
      <Link
        to="/brands"
        className="inline-flex items-center gap-1.5 text-sm text-neutral-400 hover:text-neutral-900 transition-colors mb-10"
      >
        <ArrowLeft size={14} />
        {t('brand.allBrands')}
      </Link>

      <div className="mb-8">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 className="text-4xl lg:text-5xl font-bold text-neutral-900 tracking-tight">{brand.name_en}</h1>
            {brand.name_ja && (
              <p className="text-lg text-neutral-400 mt-1">{brand.name_ja}</p>
            )}
          </div>
          <PriceRangeBadge range={brand.price_range} size="md" />
        </div>

        {infoItems.length > 0 && (
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-neutral-500">
            {infoItems.map((item, idx) => (
              <span key={item.label}>
                {idx > 0 && <span className="text-neutral-300 mr-4">/</span>}
                <span className="text-neutral-400">{item.label}:</span>{' '}
                <span className="text-neutral-700">{item.value}</span>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-8">
        <ShippingBadge tier={brand.shipping_tier} size="md" />
        {brand.style_tags.map((tag) => (
          <StyleTag key={tag} tag={tag} />
        ))}
      </div>

      {brand.description_en && (
        <div className="mb-10">
          <p className="text-neutral-600 leading-relaxed">{brand.description_en}</p>
        </div>
      )}

      {brand.buy_guide && (
        <div className="mb-10">
          <BuyGuideCard guide={brand.buy_guide} />
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        {brand.website_jp && (
          <a
            href={brand.website_jp}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 border border-neutral-200 rounded-lg text-sm font-medium text-neutral-700 hover:border-neutral-400 hover:text-neutral-900 transition-colors"
          >
            {t('brand.jpWebsite')}
            <ExternalLink size={14} />
          </a>
        )}
        {brand.website_us && (
          <a
            href={brand.website_us}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 border border-neutral-200 rounded-lg text-sm font-medium text-neutral-700 hover:border-neutral-400 hover:text-neutral-900 transition-colors"
          >
            {t('brand.usWebsite')}
            <ExternalLink size={14} />
          </a>
        )}
      </div>
    </div>
  );
}
