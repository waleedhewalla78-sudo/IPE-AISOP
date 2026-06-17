import { forwardRef, type InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="space-y-1">
        {label && <label className="text-sm font-medium text-ipe-text">{label}</label>}
        <input
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded-md border border-ipe-border bg-white px-3 py-2 text-sm placeholder:text-ipe-text-muted focus:outline-none focus:ring-2 focus:ring-ipe-primary focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50',
            error && 'border-ipe-danger',
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-ipe-danger">{error}</p>}
      </div>
    );
  },
);
Input.displayName = 'Input';
