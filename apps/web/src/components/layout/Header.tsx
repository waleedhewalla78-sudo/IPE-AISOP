import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { Bell, ChevronDown, LogOut, Moon, Sun, User } from 'lucide-react';
import type { RootState } from '@/store/store';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/features/auth/hooks/useAuth';
import { t } from '@/lib/i18n';
import api from '@/lib/api';
import { ROUTES } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { ApprovalPanel } from '@/features/approvals/components/ApprovalPanel';
import { GlobalSearch } from './GlobalSearch';
import { DemoRoleSwitcher } from './DemoRoleSwitcher';

type Notif = {
  notification_id: string;
  subject: string;
  body: string;
  channel: string;
  priority: string;
  status: string;
};

export function Header() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const user = useSelector((state: RootState) => state.auth.user);
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [items, setItems] = useState<Notif[]>([]);
  const [unread, setUnread] = useState(0);
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'));
  const panelRef = useRef<HTMLDivElement>(null);
  const profileRef = useRef<HTMLDivElement>(null);

  const userId = user?.id ?? user?.email ?? 'deploy-user';
  const displayName = user?.full_name ?? user?.email ?? 'User';
  const initial = (displayName.trim()[0] || 'U').toUpperCase();

  const refresh = useCallback(async () => {
    try {
      const [listRes, sumRes] = await Promise.all([
        api.get<Notif[]>(`/api/v1/notifications/user/${encodeURIComponent(String(userId))}`),
        api.get<{ total: number; unread: number }>(
          `/api/v1/notifications/user/${encodeURIComponent(String(userId))}/summary`,
        ),
      ]);
      setItems(Array.isArray(listRes.data) ? listRes.data : []);
      setUnread(sumRes.data?.unread ?? 0);
    } catch {
      setItems([]);
      setUnread(0);
    }
  }, [userId]);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 60_000);
    return () => window.clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    if (!open && !profileOpen) return;
    const onDoc = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) setOpen(false);
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) setProfileOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open, profileOpen]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleDark = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle('dark', next);
    try {
      localStorage.setItem('ipe-theme', next ? 'dark' : 'light');
    } catch {
      /* ignore */
    }
  };

  const markRead = async (id: string) => {
    try {
      await api.post(`/api/v1/notifications/${id}/read`);
      await refresh();
    } catch {
      /* ignore */
    }
  };

  const openNotif = async (n: Notif) => {
    await markRead(n.notification_id);
    setOpen(false);
    const p = (n.priority || '').toUpperCase();
    if (p === 'CRITICAL' || p === 'HIGH') {
      navigate(ROUTES.PLANNING_CONTROL_TOWER);
    } else if ((n.subject + n.body).toLowerCase().includes('odoo') || (n.subject + n.body).toLowerCase().includes('sync')) {
      navigate(ROUTES.PLATFORM_ODOO_CONFIG);
    } else {
      navigate(ROUTES.PLANNING_CONTROL_TOWER);
    }
  };

  return (
    <header className="flex h-header items-center gap-4 border-b border-ipe-border bg-ipe-surface-card px-4 lg:px-6">
      <div className="hidden min-w-[4rem] shrink lg:block" aria-hidden />
      <div className="flex flex-1 justify-center px-2">
        <GlobalSearch />
      </div>
      <div className="flex items-center gap-2 sm:gap-3">
        <DemoRoleSwitcher />
        <ApprovalPanel />
        <div className="relative" ref={panelRef}>
          <button
            type="button"
            className="relative rounded-lg p-2 text-ipe-text hover:bg-ipe-surface-alt"
            aria-label={t('header.notifications', 'Notifications')}
            onClick={() => {
              setOpen((v) => !v);
              void refresh();
            }}
          >
            <Bell size={18} strokeWidth={2} aria-hidden />
            {unread > 0 ? (
              <span className="absolute -end-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
                {unread > 99 ? '99+' : unread}
              </span>
            ) : null}
          </button>
          {open ? (
            <div className="absolute end-0 z-50 mt-2 w-80 overflow-hidden rounded-xl border border-ipe-border bg-ipe-surface-card shadow-lg">
              <div className="flex items-center justify-between border-b border-ipe-border px-3 py-2">
                <p className="text-sm font-semibold">{t('header.notificationCenter', 'Notification Center')}</p>
                <button type="button" className="text-xs text-ipe-primary" onClick={() => void refresh()}>
                  {t('header.refresh', 'Refresh')}
                </button>
              </div>
              <ul className="max-h-80 overflow-y-auto">
                {items.length === 0 ? (
                  <li className="px-3 py-6 text-center text-sm text-ipe-text-muted">
                    {t('header.noNotifications', 'No notifications')}
                  </li>
                ) : (
                  items.map((n) => (
                    <li key={n.notification_id}>
                      <button
                        type="button"
                        className={cn(
                          'w-full border-b border-ipe-border px-3 py-2 text-start hover:bg-ipe-surface-alt',
                          n.status !== 'read' && 'bg-ipe-primary/5',
                        )}
                        onClick={() => void openNotif(n)}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'rounded px-1.5 py-0.5 text-[10px] font-bold uppercase',
                              n.priority?.toUpperCase() === 'CRITICAL' && 'bg-red-100 text-red-700',
                              n.priority?.toUpperCase() === 'HIGH' && 'bg-amber-100 text-amber-800',
                              !['CRITICAL', 'HIGH'].includes((n.priority || '').toUpperCase()) &&
                                'bg-slate-100 text-slate-600',
                            )}
                          >
                            {n.priority || 'info'}
                          </span>
                          <span className="truncate text-sm font-medium text-ipe-text">{n.subject}</span>
                        </div>
                        <p className="mt-0.5 line-clamp-2 text-xs text-ipe-text-muted">{n.body}</p>
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </div>
          ) : null}
        </div>

        <div className="relative" ref={profileRef}>
          <button
            type="button"
            className="flex items-center gap-2 rounded-lg py-1 pe-1 ps-1 hover:bg-ipe-surface-alt sm:pe-2"
            onClick={() => setProfileOpen((v) => !v)}
            aria-expanded={profileOpen}
            aria-haspopup="menu"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ipe-primary text-xs font-bold text-white">
              {initial}
            </span>
            <span className="hidden max-w-[120px] truncate text-sm font-medium text-ipe-text sm:inline">
              {displayName}
            </span>
            <ChevronDown size={14} className="hidden text-ipe-text-muted sm:inline" aria-hidden />
          </button>
          {profileOpen ? (
            <div
              role="menu"
              className="absolute end-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-ipe-border bg-ipe-surface-card py-1 shadow-lg"
            >
              <button
                type="button"
                role="menuitem"
                className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-ipe-surface-alt"
                onClick={() => {
                  setProfileOpen(false);
                  navigate(ROUTES.WORKSPACE);
                }}
              >
                <User size={14} aria-hidden />
                {t('header.profile', 'Profile & lens')}
              </button>
              <button
                type="button"
                role="menuitem"
                className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-ipe-surface-alt"
                onClick={toggleDark}
              >
                {dark ? <Sun size={14} aria-hidden /> : <Moon size={14} aria-hidden />}
                {dark
                  ? t('header.lightMode', 'Light mode')
                  : t('header.darkMode', 'Dark mode')}
              </button>
              <div className="my-1 border-t border-ipe-border" />
              <button
                type="button"
                role="menuitem"
                className="flex w-full items-center gap-2 px-3 py-2 text-sm text-ipe-danger hover:bg-ipe-surface-alt"
                onClick={handleLogout}
              >
                <LogOut size={14} aria-hidden />
                {t('header.signOut', 'Sign out')}
              </button>
            </div>
          ) : null}
        </div>
        <Button variant="ghost" size="sm" className="hidden" onClick={handleLogout}>
          {t('header.signOut')}
        </Button>
      </div>
    </header>
  );
}
