/** Parchment tile with a thick coffee outline. Optional titled header strip. */

import type { ReactNode } from "react";

export interface PixelPanelProps {
  title?: string;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}

export function PixelPanel({
  title,
  className = "",
  bodyClassName = "",
  children,
}: PixelPanelProps) {
  return (
    <section className={`pixel-panel ${className}`}>
      {title && (
        <header className="border-b-4 border-coffee bg-surface-high px-3 py-2">
          <h2 className="font-display text-sm font-bold text-secondary">{title}</h2>
        </header>
      )}
      <div className={`p-4 ${bodyClassName}`}>{children}</div>
    </section>
  );
}
