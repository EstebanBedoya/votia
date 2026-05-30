"use client";

/**
 * "ENERGÍA" gauge — real OpenRouter credit budget. Full bar = budget intact;
 * it drains as tokens are consumed. Polls /api/usage and re-checks periodically.
 */

import { useEffect, useState } from "react";

import { PixelProgress } from "@/components/PixelProgress";
import type { UsageResponse } from "@/lib/types";

const PIPS = 10;
const REFRESH_MS = 60_000;

export function EnergyBar() {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch("/api/usage");
        if (!res.ok) throw new Error();
        const data = (await res.json()) as UsageResponse;
        if (alive) {
          setUsage(data);
          setError(false);
        }
      } catch {
        if (alive) setError(true);
      }
    };
    void load();
    const id = setInterval(load, REFRESH_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const pct = usage?.pct ?? null;
  const pips = pct == null ? 0 : Math.round((pct / 100) * PIPS);
  const label = error
    ? "—"
    : pct == null
      ? usage
        ? "∞"
        : "…"
      : `${Math.round(pct)}/100`;

  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="pixel-label">Energía</span>
        <span
          className="font-mono text-xs font-bold text-coffee tabular-nums"
          title={
            usage
              ? `Créditos OpenRouter: ${usage.remaining.toFixed(2)} de ${usage.total.toFixed(2)} restantes`
              : undefined
          }
        >
          {label}
        </span>
      </div>
      <PixelProgress value={pips} max={PIPS} className="mt-1.5" />
    </div>
  );
}
