import { create } from 'zustand';
import { translations } from '@/i18n';

type Locale = 'en' | 'zh';

interface LocaleState {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const getInitialLocale = (): Locale => {
  const stored = localStorage.getItem('locale');
  if (stored === 'en' || stored === 'zh') return stored;
  return 'en';
};

export const useLocaleStore = create<LocaleState>((set) => ({
  locale: getInitialLocale(),
  setLocale: (locale) => {
    localStorage.setItem('locale', locale);
    set({ locale });
  },
}));

export function useT() {
  const locale = useLocaleStore((s) => s.locale);

  return function t(key: string, params?: Record<string, string | number>): string {
    let text = translations[locale]?.[key] ?? translations.en[key] ?? key;
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        text = text.replaceAll(`{${k}}`, String(v));
      }
    }
    return text;
  };
}
