/**
 * Global FeasibilityDrawer context — any FeasibilityBadge can open it (STREAM-6.2).
 */
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  FeasibilityDrawer,
  type FeasibilityDrawerPayload,
} from './FeasibilityDrawer';

interface FeasibilityDrawerContextValue {
  openFeasibility: (payload: FeasibilityDrawerPayload) => void;
  closeFeasibility: () => void;
}

const FeasibilityDrawerContext = createContext<FeasibilityDrawerContextValue | null>(null);

export function FeasibilityDrawerProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [payload, setPayload] = useState<FeasibilityDrawerPayload | null>(null);

  const openFeasibility = useCallback((next: FeasibilityDrawerPayload) => {
    setPayload(next);
    setOpen(true);
  }, []);

  const closeFeasibility = useCallback(() => {
    setOpen(false);
  }, []);

  const value = useMemo(
    () => ({ openFeasibility, closeFeasibility }),
    [openFeasibility, closeFeasibility],
  );

  return (
    <FeasibilityDrawerContext.Provider value={value}>
      {children}
      <FeasibilityDrawer open={open} payload={payload} onClose={closeFeasibility} />
    </FeasibilityDrawerContext.Provider>
  );
}

export function useFeasibilityDrawer(): FeasibilityDrawerContextValue {
  const ctx = useContext(FeasibilityDrawerContext);
  if (!ctx) {
    return {
      openFeasibility: () => {
        /* no-op outside provider */
      },
      closeFeasibility: () => undefined,
    };
  }
  return ctx;
}
