import { describe, expect, it } from 'vitest';
import { t, setLocale } from '@/lib/i18n';

describe('Release 1 i18n', () => {
  it('has Arabic control tower title', () => {
    setLocale('ar');
    expect(t('controlTower.title')).toBe('برج المراقبة');
  });

  it('has English resolution title', () => {
    setLocale('en');
    expect(t('resolution.title')).toBe('Resolution Center');
  });

  it('has Arabic login title', () => {
    setLocale('ar');
    expect(t('login.title')).toContain('IPE');
  });

  it('has Arabic resolution unresolved label', () => {
    setLocale('ar');
    expect(t('resolution.unresolvedMos')).toBe('أوامر غير محلولة');
  });
});
