import { useState } from 'react';
import { getLocale, setLocale, type Locale, t } from '@/lib/i18n';

export function LanguageSwitcher() {
  const [locale, setLoc] = useState<Locale>(getLocale());

  const toggle = () => {
    const next: Locale = locale === 'ar' ? 'en' : 'ar';
    setLocale(next);
    setLoc(next);
    window.location.reload();
  };

  return (
    <button
      type="button"
      onClick={toggle}
      className="rounded border border-ipe-border px-2 py-1 text-xs text-ipe-text-muted hover:bg-ipe-surface-alt"
      title={t('nav.language')}
    >
      {locale === 'ar' ? 'EN' : 'عربي'}
    </button>
  );
}
