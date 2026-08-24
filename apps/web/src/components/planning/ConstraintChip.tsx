/**
 * ConstraintChip — type-colored pill for primary APS constraints.
 */
import { cn } from '@/lib/utils';
import { t } from '@/lib/i18n';
import {
  constraintChipClass,
  constraintIcon,
  constraintKind,
  constraintLabelKey,
} from '@/lib/scoreVisuals';

interface ConstraintChipProps {
  type: string | null | undefined;
  label?: string;
  showIcon?: boolean;
  className?: string;
}

export function ConstraintChip({
  type,
  label,
  showIcon = true,
  className,
}: ConstraintChipProps) {
  if (!type) return null;
  const kind = constraintKind(type);
  const text =
    label ??
    t(constraintLabelKey(type), type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()));

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize',
        constraintChipClass(type),
        className,
      )}
      data-testid="constraint-chip"
      data-kind={kind}
    >
      {showIcon ? <span aria-hidden>{constraintIcon(type)}</span> : null}
      {text}
    </span>
  );
}
