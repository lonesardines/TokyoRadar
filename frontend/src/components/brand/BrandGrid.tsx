import type { Brand } from '@/types';
import { useT } from '@/store/localeStore';
import BrandCard from './BrandCard';

interface BrandGridProps {
  brands: Brand[];
}

export default function BrandGrid({ brands }: BrandGridProps) {
  const t = useT();

  if (brands.length === 0) {
    return (
      <div className="text-center py-20">
        <p className="text-neutral-400 text-sm tracking-wide">{t('brands.emptyState')}</p>
        <p className="text-neutral-300 text-xs mt-2">{t('brands.adjustFilters')}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {brands.map((brand) => (
        <BrandCard key={brand.id} brand={brand} />
      ))}
    </div>
  );
}
