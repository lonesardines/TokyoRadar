import { memo } from 'react';
import { Link } from 'react-router-dom';
import type { Brand } from '@/types';
import ShippingBadge from '@/components/common/ShippingBadge';
import PriceRangeBadge from '@/components/common/PriceRangeBadge';
import StyleTag from '@/components/common/StyleTag';

interface BrandCardProps {
  brand: Brand;
}

const BrandCard = memo(function BrandCard({ brand }: BrandCardProps) {
  return (
    <Link
      to={`/brands/${brand.slug}`}
      className="group block border border-neutral-200 rounded-lg p-6 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-neutral-100 hover:border-neutral-300 bg-white"
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <h3 className="text-lg font-bold text-neutral-900 tracking-tight truncate group-hover:text-neutral-600 transition-colors">
            {brand.name_en}
          </h3>
          {brand.name_ja && (
            <p className="text-xs text-neutral-400 mt-0.5 truncate">{brand.name_ja}</p>
          )}
        </div>
        <PriceRangeBadge range={brand.price_range} />
      </div>

      {brand.style_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {brand.style_tags.slice(0, 3).map((tag) => (
            <StyleTag key={tag} tag={tag} />
          ))}
          {brand.style_tags.length > 3 && (
            <span className="text-[11px] text-neutral-400 self-center ml-1">
              +{brand.style_tags.length - 3}
            </span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between mt-auto pt-3 border-t border-neutral-100">
        <ShippingBadge tier={brand.shipping_tier} />
        {brand.headquarters && (
          <span className="text-[11px] text-neutral-400 tracking-wide">{brand.headquarters}</span>
        )}
      </div>
    </Link>
  );
});

export default BrandCard;
