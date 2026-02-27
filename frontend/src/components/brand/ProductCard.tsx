import { memo, useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import type { Item, PriceListing } from '@/types';
import { useT } from '@/store/localeStore';

interface ProductCardProps {
  item: Item;
}

const MAX_SIZES = 4;

function PriceComparisonRow({ listing, officialPrice }: { listing: PriceListing; officialPrice: number | null }) {
  const t = useT();
  const retailerPrice = listing.price_usd != null ? Number(listing.price_usd) : null;

  let diffLabel = '';
  let diffColor = 'text-neutral-400';

  if (retailerPrice != null && officialPrice != null && officialPrice > 0) {
    const pct = Math.round(((retailerPrice - officialPrice) / officialPrice) * 100);
    if (pct < 0) {
      diffLabel = t('brand.cheaper', { pct: String(Math.abs(pct)) });
      diffColor = 'text-green-600';
    } else if (pct > 0) {
      diffLabel = t('brand.moreExpensive', { pct: String(pct) });
      diffColor = 'text-red-500';
    } else {
      diffLabel = t('brand.samePrice');
      diffColor = 'text-neutral-400';
    }
  }

  const row = (
    <div className="flex items-center justify-between gap-2 py-1">
      <span className="text-[11px] text-neutral-600 truncate max-w-[80px]">
        {listing.retailer_name}
      </span>
      <div className="flex items-center gap-1.5">
        {retailerPrice != null && (
          <span className="text-[11px] font-medium text-neutral-800">
            ${retailerPrice.toFixed(2)}
          </span>
        )}
        {diffLabel && (
          <span className={`text-[10px] font-medium ${diffColor}`}>
            {diffLabel}
          </span>
        )}
        {!listing.in_stock && (
          <span className="text-[10px] text-neutral-300">OOS</span>
        )}
        {listing.url && <ExternalLink size={9} className="text-neutral-300" />}
      </div>
    </div>
  );

  if (listing.url) {
    return (
      <a href={listing.url} target="_blank" rel="noopener noreferrer" className="block hover:bg-neutral-50 -mx-1 px-1 rounded">
        {row}
      </a>
    );
  }
  return row;
}

const ProductCard = memo(function ProductCard({ item }: ProductCardProps) {
  const t = useT();
  const [showListings, setShowListings] = useState(false);

  const overflowCount = item.sizes && item.sizes.length > MAX_SIZES
    ? item.sizes.length - MAX_SIZES
    : 0;

  const allListings = item.price_listings ?? [];
  // Filter out official/self-store listings — their price is already shown as the main price
  const OFFICIAL_SLUGS = new Set(['nanamica-us', 'brand-official-jp']);
  const listings = allListings.filter(l => !OFFICIAL_SLUGS.has(l.retailer_slug));
  const officialListing = allListings.find(l => OFFICIAL_SLUGS.has(l.retailer_slug));
  const hasListings = listings.length > 0;
  const officialPrice = item.price_usd != null ? Number(item.price_usd) : null;

  // Find the best (lowest) price across all third-party channels
  const retailerPrices = listings.filter(l => l.price_usd != null).map(l => Number(l.price_usd));
  const allPrices = [
    ...(officialPrice != null ? [officialPrice] : []),
    ...retailerPrices,
  ];
  const bestPrice = allPrices.length > 0 ? Math.min(...allPrices) : null;
  const hasBetterPrice = bestPrice != null && officialPrice != null && bestPrice < officialPrice;

  const card = (
    <div className="group border border-neutral-200 rounded-lg bg-white overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-neutral-100 hover:border-neutral-300">
      {/* Image */}
      <div className="relative aspect-[3/4] overflow-hidden bg-neutral-100">
        {item.primary_image_url ? (
          <img
            src={item.primary_image_url}
            alt={item.name_en}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-300 text-xs">
            No image
          </div>
        )}
        {/* Channel count badge — total = third-party + official (if exists) */}
        {hasListings && (
          <div className="absolute top-2 right-2 bg-white/90 backdrop-blur-sm rounded-full px-2 py-0.5 text-[10px] font-medium text-neutral-700 shadow-sm">
            {t('brand.channels', { count: String(listings.length + (officialListing || officialPrice != null ? 1 : 0)) })}
          </div>
        )}
      </div>

      {/* Details */}
      <div className="p-4 space-y-2">
        <h3 className="text-sm font-medium text-neutral-900 leading-snug line-clamp-2">
          {item.name_en}
        </h3>

        <div className="flex items-center gap-2">
          {officialPrice != null && (
            <span className={`text-sm font-semibold ${hasBetterPrice ? 'text-neutral-400 line-through' : 'text-neutral-900'}`}>
              ${officialPrice.toFixed(2)}
            </span>
          )}
          {hasBetterPrice && bestPrice != null && (
            <span className="text-sm font-semibold text-green-600">
              ${bestPrice.toFixed(2)}
            </span>
          )}
          {item.compare_at_price_usd != null && Number(item.compare_at_price_usd) > (officialPrice ?? 0) && !hasBetterPrice && (
            <span className="text-xs text-neutral-400 line-through">
              ${Number(item.compare_at_price_usd).toFixed(2)}
            </span>
          )}
          {officialPrice != null && hasListings && (
            <span className="text-[10px] text-neutral-400">
              {t('brand.officialPrice')}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {item.item_type && (
            <span className="inline-block px-2 py-0.5 text-[11px] font-medium bg-neutral-100 text-neutral-600 rounded">
              {item.item_type}
            </span>
          )}
          {item.season_code && (
            <span className="inline-block px-2 py-0.5 text-[11px] font-medium bg-neutral-800 text-white rounded">
              {item.season_code}
            </span>
          )}
          {item.in_stock != null && (
            <span className="inline-flex items-center gap-1 text-[11px] text-neutral-500">
              <span className={`w-1.5 h-1.5 rounded-full ${item.in_stock ? 'bg-green-500' : 'bg-neutral-300'}`} />
              {item.in_stock ? 'In stock' : 'Out of stock'}
            </span>
          )}
        </div>

        {item.sizes && item.sizes.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {item.sizes.slice(0, MAX_SIZES).map((size) => (
              <span
                key={size}
                className="px-1.5 py-0.5 text-[10px] text-neutral-500 border border-neutral-200 rounded"
              >
                {size}
              </span>
            ))}
            {overflowCount > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] text-neutral-400">
                +{overflowCount}
              </span>
            )}
          </div>
        )}

        {/* Price comparison toggle */}
        {hasListings && (
          <div className="pt-1">
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setShowListings(!showListings);
              }}
              className="inline-flex items-center gap-1 text-[11px] text-neutral-500 hover:text-neutral-700 transition-colors"
            >
              {t('brand.compareChannels')}
              {showListings ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>

            {showListings && (
              <div className="mt-1.5 pt-1.5 border-t border-neutral-100 space-y-0">
                {listings.map((listing) => (
                  <PriceComparisonRow
                    key={listing.id}
                    listing={listing}
                    officialPrice={officialPrice}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {!hasListings && item.source_url && (
          <div className="pt-1">
            <span className="inline-flex items-center gap-1 text-[11px] text-neutral-400 group-hover:text-neutral-600 transition-colors">
              {t('brand.viewProduct')}
              <ExternalLink size={10} />
            </span>
          </div>
        )}
      </div>
    </div>
  );

  // Only wrap in <a> if no price listings (otherwise we have inner links)
  if (item.source_url && !hasListings) {
    return (
      <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="block">
        {card}
      </a>
    );
  }

  return card;
});

export default ProductCard;
