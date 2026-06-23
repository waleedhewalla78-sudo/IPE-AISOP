import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import type { RootState } from '@/store/store';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/features/auth/hooks/useAuth';

export function Header() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const user = useSelector((state: RootState) => state.auth.user);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-ipe-border bg-white px-6">
      <span className="text-sm font-medium text-ipe-text">Intelligent Planning Engine</span>
      <div className="flex items-center gap-4">
        <span className="text-sm text-ipe-text-muted">
          {user?.full_name ?? user?.email ?? 'User'}
        </span>
        <Button variant="secondary" size="sm" onClick={handleLogout}>
          Sign out
        </Button>
      </div>
    </header>
  );
}
