import { cn } from '@/lib/utils';

interface StyleTagProps {
  tag: string;
  active?: boolean;
  onClick?: () => void;
}

export default function StyleTag({ tag, active = false, onClick }: StyleTagProps) {
  const isButton = !!onClick;
  const Component = isButton ? 'button' : 'span';

  return (
    <Component
      onClick={onClick}
      className={cn(
        'inline-flex items-center rounded-full border text-[11px] font-medium tracking-wide uppercase transition-all',
        'px-3 py-1',
        active
          ? 'border-neutral-900 bg-neutral-900 text-white'
          : 'border-neutral-200 bg-white text-neutral-500',
        isButton && !active && 'hover:border-neutral-400 hover:text-neutral-700 cursor-pointer',
        isButton && active && 'cursor-pointer'
      )}
    >
      {tag}
    </Component>
  );
}
