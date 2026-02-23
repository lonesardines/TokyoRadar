import { useT } from '@/store/localeStore';

export default function Footer() {
  const t = useT();

  return (
    <footer className="border-t border-neutral-200 bg-white">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-10">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-baseline gap-0.5">
            <span className="text-sm font-light tracking-tight text-neutral-400">TOKYO</span>
            <span className="text-sm font-black tracking-tight text-neutral-400">RADAR</span>
            <span className="text-xs text-neutral-300 ml-2">&copy; 2026</span>
          </div>
          <p className="text-xs text-neutral-400 tracking-wide">
            {t('footer.tagline')}
          </p>
        </div>
      </div>
    </footer>
  );
}
