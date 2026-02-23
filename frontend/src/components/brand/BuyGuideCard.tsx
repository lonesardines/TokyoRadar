import type { BuyGuide } from '@/types';
import { useT } from '@/store/localeStore';
import ShippingBadge from '@/components/common/ShippingBadge';

interface BuyGuideCardProps {
  guide: BuyGuide;
}

export default function BuyGuideCard({ guide }: BuyGuideCardProps) {
  const t = useT();

  return (
    <div className="border border-neutral-200 rounded-lg overflow-hidden">
      <div className="px-6 py-4 bg-neutral-50 border-b border-neutral-200">
        <h3 className="text-sm font-semibold text-neutral-900 uppercase tracking-wide">{t('brand.howToBuy')}</h3>
      </div>
      {guide.summary && (
        <div className="px-6 py-4 border-b border-neutral-100">
          <p className="text-sm text-neutral-600 leading-relaxed">{guide.summary}</p>
        </div>
      )}
      <div className="divide-y divide-neutral-100">
        {guide.best_channels.map((channel, idx) => (
          <a
            key={idx}
            href={channel.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-4 flex items-start justify-between gap-4 hover:bg-neutral-50 transition-colors block"
          >
            <div className="min-w-0">
              <p className="text-sm font-medium text-neutral-900">{channel.name}</p>
              <p className="text-xs text-neutral-500 mt-1 leading-relaxed">{channel.notes}</p>
            </div>
            <ShippingBadge tier={channel.tier} />
          </a>
        ))}
      </div>
    </div>
  );
}
