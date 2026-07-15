import { useEffect, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { CopilotPanel } from './CopilotPanel';
import { t } from '@/lib/i18n';

/**
 * Global Ctrl/Cmd+K floating Copilot (UI/UX structural analysis P2).
 * Does not replace the dedicated Copilot route — opens a side drawer from any screen.
 */
export function CopilotCommandPalette({ children }: { children?: ReactNode }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <>
      {children}
      <button
        type="button"
        className="fixed bottom-5 end-5 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-ipe-primary text-white shadow-lg hover:bg-ipe-primary/90 md:bottom-6 md:end-6"
        aria-label={t('copilot.openShortcut')}
        title={`${t('copilot.openShortcut')} (Ctrl+K)`}
        onClick={() => setOpen(true)}
      >
        <span className="text-lg font-semibold" aria-hidden>
          AI
        </span>
      </button>
      {open
        ? createPortal(
            <div className="fixed inset-0 z-50 flex justify-end">
              <button
                type="button"
                className="absolute inset-0 bg-black/30"
                aria-label={t('copilot.close')}
                onClick={() => setOpen(false)}
              />
              <div className="relative flex h-full w-full max-w-md flex-col border-s border-ipe-border bg-white shadow-xl">
                <div className="flex items-center justify-between border-b border-ipe-border px-4 py-3">
                  <div>
                    <p className="font-semibold text-ipe-text">{t('copilot.title')}</p>
                    <p className="text-xs text-ipe-text-muted">{t('copilot.shortcutHint')}</p>
                  </div>
                  <button
                    type="button"
                    className="rounded px-2 py-1 text-sm text-ipe-text-muted hover:bg-ipe-surface-alt"
                    onClick={() => setOpen(false)}
                  >
                    {t('copilot.close')}
                  </button>
                </div>
                <div className="min-h-0 flex-1 overflow-auto p-4">
                  <CopilotPanel />
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}
