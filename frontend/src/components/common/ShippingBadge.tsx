import { cn } from '@/lib/utils';
import { useT } from '@/store/localeStore';

interface ShippingBadgeProps {
  tier: 'green' | 'yellow' | 'red';
  size?: 'sm' | 'md';
}

const tierConfig = {
  green: {
    labelKey: 'shipping.green',
    dotColor: 'bg-shipping-green',
    bgColor: 'bg-green-50',
    textColor: 'text-green-800',
    borderColor: 'border-green-200',
  },
  yellow: {
    labelKey: 'shipping.yellow',
    dotColor: 'bg-shipping-yellow',
    bgColor: 'bg-amber-50',
    textColor: 'text-amber-800',
    borderColor: 'border-amber-200',
  },
  red: {
    labelKey: 'shipping.red',
    dotColor: 'bg-shipping-red',
    bgColor: 'bg-red-50',
    textColor: 'text-red-800',
    borderColor: 'border-red-200',
  },
};

export default function ShippingBadge({ tier, size = 'sm' }: ShippingBadgeProps) {
  const config = tierConfig[tier];
  const t = useT();

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        config.bgColor,
        config.textColor,
        config.borderColor,
        size === 'sm' ? 'px-2.5 py-0.5 text-[11px]' : 'px-3.5 py-1 text-xs'
      )}
    >
      <span className={cn('rounded-full', config.dotColor, size === 'sm' ? 'h-1.5 w-1.5' : 'h-2 w-2')} />
      {t(config.labelKey)}
    </span>
  );
}
