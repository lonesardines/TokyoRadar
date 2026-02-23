import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLocaleStore, useT } from '@/store/localeStore';

export default function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const t = useT();
  const { locale, setLocale } = useLocaleStore();

  const navItems = [
    { to: '/brands', label: t('nav.brands') },
    { to: '/retailers', label: t('nav.retailers') },
    { to: '/buy-guide', label: t('nav.buyGuide') },
  ];

  const langSwitcher = (
    <div className="inline-flex items-center rounded-md border border-neutral-200 overflow-hidden text-xs font-medium">
      <button
        onClick={() => setLocale('en')}
        className={cn(
          'px-2.5 py-1.5 transition-colors',
          locale === 'en'
            ? 'bg-neutral-900 text-white'
            : 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50'
        )}
      >
        EN
      </button>
      <button
        onClick={() => setLocale('zh')}
        className={cn(
          'px-2.5 py-1.5 transition-colors',
          locale === 'zh'
            ? 'bg-neutral-900 text-white'
            : 'text-neutral-500 hover:text-neutral-900 hover:bg-neutral-50'
        )}
      >
        中
      </button>
    </div>
  );

  return (
    <header className="border-b border-neutral-200 bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          <Link to="/" className="flex items-baseline gap-0.5 group">
            <span className="text-2xl lg:text-3xl font-light tracking-tight text-neutral-900 transition-colors group-hover:text-neutral-600">
              TOKYO
            </span>
            <span className="text-2xl lg:text-3xl font-black tracking-tight text-neutral-900 transition-colors group-hover:text-neutral-600">
              RADAR
            </span>
            <span className="hidden sm:inline-block ml-3 text-[10px] tracking-widest text-neutral-400 font-normal uppercase">
              日潮情报雷达
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'text-sm font-medium tracking-wide uppercase transition-colors',
                    isActive
                      ? 'text-neutral-900'
                      : 'text-neutral-400 hover:text-neutral-700'
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
            {langSwitcher}
          </nav>

          <div className="flex items-center gap-3 md:hidden">
            {langSwitcher}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 -mr-2 text-neutral-600 hover:text-neutral-900 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <nav className="md:hidden pb-6 pt-2 border-t border-neutral-100">
            <div className="flex flex-col gap-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'px-3 py-3 text-sm font-medium tracking-wide uppercase transition-colors rounded-lg',
                      isActive
                        ? 'text-neutral-900 bg-neutral-50'
                        : 'text-neutral-400 hover:text-neutral-700 hover:bg-neutral-50'
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
