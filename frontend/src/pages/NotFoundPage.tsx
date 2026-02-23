import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useT } from '@/store/localeStore';

export default function NotFoundPage() {
  const t = useT();

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-8 py-32 text-center">
      <p className="text-8xl font-black text-neutral-100 mb-4">404</p>
      <h1 className="text-xl font-bold text-neutral-900 mb-2">{t('notFound.title')}</h1>
      <p className="text-sm text-neutral-400 mb-8">{t('notFound.description')}</p>
      <Link
        to="/"
        className="inline-flex items-center gap-2 px-5 py-2.5 bg-neutral-900 text-white text-sm font-medium rounded-lg hover:bg-neutral-800 transition-colors"
      >
        <ArrowLeft size={14} />
        {t('notFound.backHome')}
      </Link>
    </div>
  );
}
