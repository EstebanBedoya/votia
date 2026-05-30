/**
 * Retro window title bar. ALL-CAPS title with a 2px drop shadow (DESIGN.md rule),
 * a "connected" status pip, and decorative window controls on the right.
 */

import Link from "next/link";

import { PixelIcon } from "@/components/PixelIcon";

export interface TitleBarProps {
  title: string;
  /** Optional status text shown under the title (e.g. "CONECTADO"). */
  status?: string;
}

export function TitleBar({ title, status = "CONECTADO" }: TitleBarProps) {
  return (
    <header className="pixel-panel flex items-center justify-between gap-4 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <Link
          href="/"
          aria-label="Inicio"
          className="grid h-9 w-9 shrink-0 place-items-center border-2 border-coffee bg-gold text-coffee transition-transform hover:-translate-y-0.5 pixel-shadow"
        >
          <PixelIcon name="bird" size={22} />
        </Link>
        <div className="min-w-0">
          <h1
            className="font-display truncate text-base font-bold text-secondary md:text-lg"
            style={{ textShadow: "2px 2px 0 var(--color-gold)" }}
          >
            {title}
          </h1>
          {status && (
            <span className="mt-1 inline-flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 border-2 border-coffee bg-emerald" />
              <span className="pixel-label text-emerald">{status}</span>
            </span>
          )}
        </div>
      </div>

      <nav className="flex shrink-0 items-center gap-2">
        {[
          { href: "/chat", label: "CHAT" },
          { href: "/radar", label: "RADAR" },
        ].map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="hidden border-2 border-coffee bg-surface-low px-3 py-1.5 pixel-label hover:bg-gold sm:block"
          >
            {l.label}
          </Link>
        ))}
        {(["share", "copy", "chevron"] as const).map((g) => (
          <span
            key={g}
            aria-hidden
            className="grid h-7 w-7 place-items-center border-2 border-coffee bg-surface-low text-coffee"
          >
            <PixelIcon name={g} size={14} />
          </span>
        ))}
      </nav>
    </header>
  );
}
