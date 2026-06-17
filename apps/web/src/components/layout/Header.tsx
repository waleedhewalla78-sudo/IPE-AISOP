import { useSelector } from 'react-redux';
import type { RootState } from '@/store/store';

export function Header() {
  const user = useSelector((state: RootState) => state.auth.user);

  return (
    <header className="flex h-14 items-center justify-between border-b border-ipe-border bg-white px-6">
      <div />
      <div className="flex items-center gap-4">
        <span className="text-sm text-ipe-text-muted">
          {user?.full_name ?? 'Not logged in'}
        </span>
      </div>
    </header>
  );
}
