"use client";

/**
 * "ENERGÍA" gauge — the OpenRouter key's spending limit. Full bar = limit
 * intact; it drains as dollars are burned. Polls /api/key periodically. When the
 * key has no cap the limit is unknown, so we show "∞" instead of a bar fill.
 */

import { useEffect, useState } from "react";

import { PixelProgress } from "@/components/PixelProgress";
import type { KeyResponse } from "@/lib/types";

const PIPS = 10;
const REFRESH_MS = 60_000;

export function EnergyBar() {
  const [key, setKey] = useState<KeyResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const res = await fetch("/api/key");
        if (!res.ok) throw new Error();
        const data = (await res.json()) as KeyResponse;
        if (alive) {
          setKey(data);
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

  const pct = key?.pct ?? null;
  const pips = pct == null ? 0 : Math.round((pct / 100) * PIPS);
  const label = error
    ? "—"
    : pct == null
      ? key
        ? "∞"
        : "…"
      : `${Math.round(pct)}/100`;

  const tooltip =
    key && key.limit != null
      ? `Límite OpenRouter: $${key.usage.toFixed(2)} de $${key.limit.toFixed(2)} gastados`
      : key
        ? `Gastado en OpenRouter: $${key.usage.toFixed(2)} (sin límite de crédito)`
        : undefined;

  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="pixel-label">Energía</span>
        <span className="font-mono text-xs font-bold text-coffee tabular-nums" title={tooltip}>
          {label}
        </span>
      </div>
      <PixelProgress value={pips} max={PIPS} className="mt-1.5" />
    </div>
  );
}
