import { Spinner } from '@/components/ui/Spinner';

export function RouteFallback() {
  return (
    <div className="flex min-h-[12rem] items-center justify-center" role="status" aria-label="Loading page">
      <Spinner size="lg" />
    </div>
  );
}
