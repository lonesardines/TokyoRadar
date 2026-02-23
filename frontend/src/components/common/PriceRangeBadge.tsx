import { cn } from '@/lib/utils';
import { useT } from '@/store/localeStore';

interface PriceRangeBadgeProps {
  range: string;
  size?: 'sm' | 'md';
}

const rangeConfig: Record<string, { label: string; titleKey: string }> = {
  budget: { label: '$', titleKey: 'price.budget' },
  low_mid: { label: '$$', titleKey: 'price.low_mid' },
  mid: { label: '$$', titleKey: 'price.mid' },
  mid_high: { label: '$$$', titleKey: 'price.mid_high' },
  high: { label: '$$$$', titleKey: 'price.high' },
  luxury: { label: '$$$$$', titleKey: 'price.luxury' },
};

export default function PriceRangeBadge({ range, size = 'sm' }: PriceRangeBadgeProps) {
  const t = useT();
  const config = rangeConfig[range];
  const label = config?.label ?? range;
  const title = config ? t(config.titleKey) : range;

  return (
    <span
      title={title}
      className={cn(
        'inline-flex items-center rounded-full border border-neutral-200 bg-neutral-50 font-semibold text-neutral-600 tracking-tight',
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-3 py-1 text-xs'
      )}
    >
      {label}
    </span>
  );
}
