import { useQuery } from '@tanstack/react-query';
import { ExternalLink } from 'lucide-react';
import { getRetailers } from '@/api/retailers';
import { useT } from '@/store/localeStore';
import ShippingBadge from '@/components/common/ShippingBadge';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import type { Retailer } from '@/types';

function RetailerCard({ retailer }: { retailer: Retailer }) {
  const t = useT();

  return (
    <div className="border border-neutral-200 rounded-lg p-6 hover:border-neutral-300 hover:shadow-sm transition-all">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="text-base font-bold text-neutral-900 tracking-tight">{retailer.name}</h3>
          <p className="text-xs text-neutral-400 mt-0.5">{retailer.country}</p>
        </div>
        <ShippingBadge tier={retailer.shipping_tier} />
      </div>

      {retailer.description_en && (
        <p className="text-sm text-neutral-500 leading-relaxed mb-4">{retailer.description_en}</p>
      )}

      {retailer.supported_proxies.length > 0 && (
        <div className="mb-3">
          <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest">{t('retailers.supportedProxies')}</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {retailer.supported_proxies.map((proxy) => (
              <span
                key={proxy}
                className="text-[11px] px-2 py-0.5 bg-neutral-50 border border-neutral-100 rounded text-neutral-600"
              >
                {proxy}
              </span>
            ))}
          </div>
        </div>
      )}

      {retailer.payment_methods.length > 0 && (
        <div className="mb-4">
          <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest">{t('retailers.payment')}</span>
          <p className="text-xs text-neutral-500 mt-1">{retailer.payment_methods.join(', ')}</p>
        </div>
      )}

      <a
        href={retailer.website}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-neutral-500 hover:text-neutral-900 transition-colors"
      >
        {t('retailers.visitWebsite')}
        <ExternalLink size={12} />
      </a>
    </div>
  );
}

const TIER_ORDER: ('green' | 'yellow' | 'red')[] = ['green', 'yellow', 'red'];

const TIER_ICONS: Record<string, string> = {
  green: '\u{1F7E2}',
  yellow: '\u{1F7E1}',
  red: '\u{1F534}',
};

const TIER_LABEL_KEYS: Record<string, string> = {
  green: 'retailers.directShipping',
  yellow: 'retailers.proxyRequired',
  red: 'retailers.agentRequired',
};

export default function RetailersPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['retailers'],
    queryFn: () => getRetailers({ per_page: 100 }),
  });
  const t = useT();

  const retailers = data?.data ?? [];

  const groupedRetailers = TIER_ORDER.map((tier) => ({
    tier,
    icon: TIER_ICONS[tier],
    label: t(TIER_LABEL_KEYS[tier]),
    retailers: retailers.filter((r) => r.shipping_tier === tier),
  })).filter((group) => group.retailers.length > 0);

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-10 lg:py-16">
      <div className="mb-10">
        <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-[0.3em] mb-2">{t('retailers.directory')}</p>
        <h1 className="text-3xl lg:text-4xl font-bold text-neutral-900 tracking-tight">{t('retailers.title')}</h1>
        <p className="text-sm text-neutral-400 mt-2">
          {t('retailers.subtitle')}
        </p>
      </div>

      {isLoading ? (
        <LoadingSpinner className="py-20" />
      ) : isError ? (
        <div className="text-center py-20">
          <p className="text-neutral-500 text-sm">{t('retailers.loadError')}</p>
        </div>
      ) : (
        <div className="space-y-12">
          {groupedRetailers.map((group) => (
            <section key={group.tier}>
              <h2 className="text-lg font-bold text-neutral-900 tracking-tight mb-5 flex items-center gap-2">
                <span>{group.icon}</span>
                {group.label}
                <span className="text-sm font-normal text-neutral-400">({group.retailers.length})</span>
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {group.retailers.map((retailer) => (
                  <RetailerCard key={retailer.id} retailer={retailer} />
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
