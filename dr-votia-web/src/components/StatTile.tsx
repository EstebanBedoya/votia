/**
 * A "collection" tile: axis icon, mean solidez, and a segmented bar. The whole
 * tile is a link into the axis detail page (more info per candidate).
 */

import Link from "next/link";

import { PixelIcon, type PixelIconName } from "@/components/PixelIcon";
import { PixelProgress } from "@/components/PixelProgress";

export interface StatTileProps {
  icon: PixelIconName;
  label: string;
  /** solidez 0..5 */
  value: number;
  href: string;
}

export function StatTile({ icon, label, value, href }: StatTileProps) {
  return (
    <Link
      href={href}
      aria-label={`${label}: solidez ${value.toFixed(1)} de 5 — ver detalle`}
      className="group flex flex-col items-center gap-2 border-[3px] border-coffee bg-surface-low p-3 outline-none transition-all duration-150 hover:-translate-y-1 hover:bg-surface-lowest focus-visible:ring-4 focus-visible:ring-gold pixel-shadow"
    >
      <span className="text-secondary transition-colors group-hover:text-tertiary">
        <PixelIcon name={icon} size={26} />
      </span>
      <span className="font-mono text-2xl font-bold text-secondary tabular-nums">
        {value.toFixed(1)}
      </span>
      <span className="pixel-label text-center leading-tight text-on-surface-variant">
        {label}
      </span>
      <PixelProgress value={value} max={5} />
    </Link>
  );
}
