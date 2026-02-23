import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight } from 'lucide-react';
import { getBrands } from '@/api/brands';
import { useT } from '@/store/localeStore';
import BrandCard from '@/components/brand/BrandCard';
import LoadingSpinner from '@/components/common/LoadingSpinner';

const FEATURED_SLUGS = [
  'visvim',
  'needles',
  'kapital',
  'comme-des-garcons',
  'human-made',
  'wtaps',
];

const STYLE_CATEGORIES = [
  { tag: 'streetwear' },
  { tag: 'avant-garde' },
  { tag: 'workwear' },
  { tag: 'outdoor' },
  { tag: 'denim' },
  { tag: 'luxury' },
];

export default function HomePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['brands', 'featured'],
    queryFn: () => getBrands({ per_page: 50 }),
  });
  const t = useT();

  const featuredBrands = data?.data?.filter((b) => FEATURED_SLUGS.includes(b.slug)).slice(0, 6) ?? [];

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-white">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-24 lg:py-36">
          <div className="max-w-3xl">
            <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-[0.3em] mb-6">
              {t('home.hero.badge')}
            </p>
            <h1 className="text-5xl sm:text-6xl lg:text-8xl font-black text-neutral-900 tracking-tighter leading-[0.9]">
              <span className="font-light">TOKYO</span>
              <br />
              RADAR
            </h1>
            <p className="text-neutral-400 text-sm sm:text-base mt-6 max-w-md leading-relaxed">
              {t('home.hero.subtitle')}
            </p>
            <div className="flex items-center gap-4 mt-10">
              <Link
                to="/brands"
                className="inline-flex items-center gap-2 px-6 py-3 bg-neutral-900 text-white text-sm font-medium rounded-lg hover:bg-neutral-800 transition-colors"
              >
                {t('home.hero.exploreBrands')}
                <ArrowRight size={16} />
              </Link>
              <Link
                to="/buy-guide"
                className="inline-flex items-center gap-2 px-6 py-3 border border-neutral-200 text-neutral-700 text-sm font-medium rounded-lg hover:border-neutral-400 hover:text-neutral-900 transition-colors"
              >
                {t('home.hero.buyGuide')}
              </Link>
            </div>
          </div>
          <div className="absolute top-10 right-10 lg:right-20 text-[200px] lg:text-[300px] font-black text-neutral-50 leading-none select-none pointer-events-none hidden md:block">
            JP
          </div>
        </div>
      </section>

      {/* Editor's Picks */}
      <section className="border-t border-neutral-200 bg-neutral-50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-24">
          <div className="flex items-end justify-between mb-10">
            <div>
              <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-[0.3em] mb-2">{t('home.editorsPicks.badge')}</p>
              <h2 className="text-2xl lg:text-3xl font-bold text-neutral-900 tracking-tight">{t('home.editorsPicks')}</h2>
            </div>
            <Link
              to="/brands"
              className="hidden sm:inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
            >
              {t('home.viewAllBrands')}
              <ArrowRight size={14} />
            </Link>
          </div>
          {isLoading ? (
            <LoadingSpinner className="py-20" />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {featuredBrands.map((brand) => (
                <BrandCard key={brand.id} brand={brand} />
              ))}
            </div>
          )}
          <Link
            to="/brands"
            className="sm:hidden inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 transition-colors mt-8"
          >
            {t('home.viewAllBrands')}
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>

      {/* Browse by Style */}
      <section className="border-t border-neutral-200">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-24">
          <div className="mb-10">
            <p className="text-[10px] font-medium text-neutral-400 uppercase tracking-[0.3em] mb-2">{t('home.browseByStyle.badge')}</p>
            <h2 className="text-2xl lg:text-3xl font-bold text-neutral-900 tracking-tight">{t('home.browseByStyle')}</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {STYLE_CATEGORIES.map((cat) => (
              <Link
                key={cat.tag}
                to={`/brands?style=${cat.tag}`}
                className="group border border-neutral-200 rounded-lg p-5 hover:border-neutral-400 hover:shadow-sm transition-all"
              >
                <h3 className="text-sm font-bold text-neutral-900 group-hover:text-neutral-600 transition-colors">
                  {t(`style.${cat.tag}`)}
                </h3>
                <p className="text-[11px] text-neutral-400 mt-1">{t(`style.${cat.tag}.desc`)}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="border-t border-neutral-200 bg-neutral-900">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12">
          <div className="flex flex-col sm:flex-row items-center justify-center gap-8 sm:gap-16">
            <div className="text-center">
              <p className="text-3xl font-bold text-white">50+</p>
              <p className="text-[11px] text-neutral-400 uppercase tracking-widest mt-1">{t('home.stats.brands')}</p>
            </div>
            <div className="hidden sm:block w-px h-10 bg-neutral-700" />
            <div className="text-center">
              <p className="text-3xl font-bold text-white">10+</p>
              <p className="text-[11px] text-neutral-400 uppercase tracking-widest mt-1">{t('home.stats.retailers')}</p>
            </div>
            <div className="hidden sm:block w-px h-10 bg-neutral-700" />
            <div className="text-center">
              <p className="text-3xl font-bold text-white">5</p>
              <p className="text-[11px] text-neutral-400 uppercase tracking-widest mt-1">{t('home.stats.proxyServices')}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
