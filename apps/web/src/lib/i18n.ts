import en from '@/locales/en.json';
import ar from '@/locales/ar.json';

export type Locale = 'en' | 'ar';

const bundles: Record<Locale, Record<string, string>> = { en, ar };

let currentLocale: Locale =
  (localStorage.getItem('ipe_locale') as Locale) ||
  (import.meta.env.VITE_DEFAULT_LOCALE as Locale) ||
  'en';

export function getLocale(): Locale {
  return currentLocale;
}

export function setLocale(locale: Locale): void {
  currentLocale = locale;
  localStorage.setItem('ipe_locale', locale);
  document.documentElement.lang = locale;
  document.documentElement.dir = locale === 'ar' ? 'rtl' : 'ltr';
}

export function t(key: string, fallback?: string): string {
  return bundles[currentLocale][key] ?? bundles.en[key] ?? fallback ?? key;
}

// init on load
setLocale(currentLocale);
