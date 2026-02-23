import { useQuery } from '@tanstack/react-query';
import { ExternalLink, Check, X, Clock, Truck } from 'lucide-react';
import { getProxyServices } from '@/api/proxyServices';
import { useT } from '@/store/localeStore';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import type { ProxyService } from '@/types';

const SERVICE_TYPE_KEYS: Record<string, string> = {
  proxy: 'buyguide.proxyBuying',
  forwarding: 'buyguide.packageForwarding',
  both: 'buyguide.proxyForwarding',
};

function ProxyServiceCard({ service }: { service: ProxyService }) {
  const t = useT();

  return (
    <div className="border border-neutral-200 rounded-lg overflow-hidden hover:border-neutral-300 hover:shadow-sm transition-all">
      <div className="p-6">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h3 className="text-lg font-bold text-neutral-900 tracking-tight">{service.name}</h3>
            <span className="inline-block text-[11px] font-medium text-neutral-500 bg-neutral-50 border border-neutral-100 rounded-full px-2.5 py-0.5 mt-1.5">
              {t(SERVICE_TYPE_KEYS[service.service_type] ?? service.service_type)}
            </span>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="flex items-center gap-1.5 text-neutral-500">
              <Clock size={14} />
              <span className="text-sm font-medium">{t('buyguide.days', { count: service.avg_delivery_days_us })}</span>
            </div>
            <p className="text-[10px] text-neutral-400 mt-0.5">{t('buyguide.avgToUS')}</p>
          </div>
        </div>

        {service.description_en && (
          <p className="text-sm text-neutral-500 leading-relaxed mb-5">{service.description_en}</p>
        )}

        {Object.keys(service.fee_structure).length > 0 && (
          <div className="mb-5">
            <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest block mb-2">{t('buyguide.feeStructure')}</span>
            <div className="bg-neutral-50 rounded-md p-3 space-y-1">
              {Object.entries(service.fee_structure).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-xs">
                  <span className="text-neutral-500">{key}</span>
                  <span className="text-neutral-700 font-medium">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 mb-5">
          <div>
            <span className="text-[10px] font-medium text-green-600 uppercase tracking-widest block mb-2">{t('buyguide.pros')}</span>
            <ul className="space-y-1.5">
              {service.pros.map((pro, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-xs text-neutral-600">
                  <Check size={13} className="text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{pro}</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <span className="text-[10px] font-medium text-red-500 uppercase tracking-widest block mb-2">{t('buyguide.cons')}</span>
            <ul className="space-y-1.5">
              {service.cons.map((con, idx) => (
                <li key={idx} className="flex items-start gap-1.5 text-xs text-neutral-600">
                  <X size={13} className="text-red-400 mt-0.5 flex-shrink-0" />
                  <span>{con}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {service.supported_retailers.length > 0 && (
          <div className="mb-5">
            <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest block mb-2">
              {t('buyguide.supportedRetailers')}
            </span>
            <div className="flex flex-wrap gap-1">
              {service.supported_retailers.map((retailer) => (
                <span
                  key={retailer}
                  className="text-[11px] px-2 py-0.5 bg-neutral-50 border border-neutral-100 rounded text-neutral-600"
                >
                  {retailer}
                </span>
              ))}
            </div>
          </div>
        )}

        {service.shipping_methods.length > 0 && (
          <div className="mb-5">
            <span className="text-[10px] font-medium text-neutral-400 uppercase tracking-widest block mb-2">
              {t('buyguide.shippingMethods')}
            </span>
            <div className="flex flex-wrap gap-2">
              {service.shipping_methods.map((method) => (
                <span key={method} className="inline-flex items-center gap-1 text-xs text-neutral-500">
                  <Truck size={12} />
                  {method}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="px-6 py-4 bg-neutral-50 border-t border-neutral-100">
        <a
          href={service.website}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-sm font-medium text-neutral-700 hover:text-neutral-900 transition-colors"
        >
          {t('buyguide.visit', { name: service.name })}
          <ExternalLink size={14} />
        </a>
      </div>
    </div>
  );
}

export default function BuyGuidePage() {
  const { data: services, isLoading, isError } = useQuery({
    queryKey: ['proxy-services'],
    queryFn: getProxyServices,
  });
  const t = useT();

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-10 lg:py-16">
      <div className="mb-10">
        <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-[0.3em] mb-2">{t('buyguide.badge')}</p>
        <h1 className="text-3xl lg:text-4xl font-bold text-neutral-900 tracking-tight">{t('buyguide.title')}</h1>
        <p className="text-sm text-neutral-400 mt-2 max-w-lg leading-relaxed">
          {t('buyguide.subtitle')}
        </p>
      </div>

      {/* Shipping Tier Legend */}
      <div className="mb-10 p-5 bg-neutral-50 rounded-lg border border-neutral-100">
        <h3 className="text-xs font-semibold text-neutral-900 uppercase tracking-wide mb-3">{t('buyguide.tierGuide')}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-start gap-2">
            <span className="h-3 w-3 rounded-full bg-shipping-green mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-neutral-700">{t('buyguide.directShip')}</p>
              <p className="text-[11px] text-neutral-400">{t('buyguide.directShipDesc')}</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="h-3 w-3 rounded-full bg-shipping-yellow mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-neutral-700">{t('buyguide.proxyRequired')}</p>
              <p className="text-[11px] text-neutral-400">{t('buyguide.proxyRequiredDesc')}</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="h-3 w-3 rounded-full bg-shipping-red mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-medium text-neutral-700">{t('buyguide.agentRequired')}</p>
              <p className="text-[11px] text-neutral-400">{t('buyguide.agentRequiredDesc')}</p>
            </div>
          </div>
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner className="py-20" />
      ) : isError ? (
        <div className="text-center py-20">
          <p className="text-neutral-500 text-sm">{t('buyguide.loadError')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {services?.map((service) => (
            <ProxyServiceCard key={service.id} service={service} />
          ))}
        </div>
      )}
    </div>
  );
}
