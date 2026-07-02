import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import { t } from '@/lib/i18n';
import { useAuth } from '../hooks/useAuth';
import { getAuthMode, loginWithKeycloak } from '../keycloak';

export function LoginForm() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const keycloakMode = getAuthMode() === 'keycloak';

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login({ email, password });
      navigate('/planning/dashboard');
    } catch {
      setError(t('login.error'));
    }
  };

  const handleSso = () => {
    loginWithKeycloak('/planning/dashboard');
  };

  return (
    <div className="flex h-screen items-center justify-center bg-ipe-surface">
      <Card className="w-full max-w-sm">
        <h1 className="mb-6 text-2xl font-bold text-ipe-primary">{t('login.title')}</h1>
        {keycloakMode ? (
          <div className="space-y-4">
            <p className="text-sm text-ipe-muted">{t('login.ssoHint')}</p>
            {error && <p className="text-sm text-ipe-danger">{error}</p>}
            <Button type="button" className="w-full" onClick={handleSso}>
              {t('login.sso')}
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label={t('login.email')}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('login.emailPlaceholder')}
              required
            />
            <Input
              label={t('login.password')}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('login.passwordPlaceholder')}
              required
            />
            {error && <p className="text-sm text-ipe-danger">{error}</p>}
            <Button type="submit" className="w-full">
              {t('login.submit')}
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
}
