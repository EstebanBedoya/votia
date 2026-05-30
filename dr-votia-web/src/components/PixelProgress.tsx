/** Segmented progress bar (pips, not a smooth fill). Emerald fill on the grid. */

export interface PixelProgressProps {
  /** Filled pips. */
  value: number;
  /** Total pips. */
  max?: number;
  className?: string;
}

export function PixelProgress({ value, max = 5, className = "" }: PixelProgressProps) {
  const filled = Math.max(0, Math.min(max, Math.round(value)));
  return (
    <div className={`pixel-progress ${className}`} role="img" aria-label={`${filled} de ${max}`}>
      {Array.from({ length: max }, (_, i) => (
        <span key={i} data-on={i < filled} />
      ))}
    </div>
  );
}
