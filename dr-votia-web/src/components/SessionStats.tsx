"use client";

/**
 * Session readout under the ENERGÍA gauge: how many OpenRouter dollars this
 * conversation has spent, and which model answers it.
 *
 * Spend is polled from /api/session/usage (the browser's session cookie is
 * relayed by that BFF route). The model is read once from /api/config — it does
 * not change between turns.
 */

import { useEffect, useState } from "react";

import type { ConfigResponse, SessionUsageResponse } from "@/lib/types";

const REFRESH_MS = 15_000;

/** Drop the vendor prefix for a compact label: "anthropic/claude-..." → "claude-...". */
function shortModel(slug: string): string {
  const slash = slug.indexOf("/");
  return slash === -1 ? slug : slug.slice(slash + 1);
}

export function SessionStats() {
  const [cost, setCost] = useState<number | null>(null);
  const [model, setModel] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    fetch("/api/config")
      .then((res) => (res.ok ? (res.json() as Promise<ConfigResponse>) : null))
      .then((data) => {
        if (alive && data) setModel(data.answer_model);
      })
      .catch(() => {});

    const loadCost = async () => {
      try {
        const res = await fetch("/api/session/usage");
        if (!res.ok) return;
        const data = (await res.json()) as SessionUsageResponse;
        if (alive) setCost(data.cost_usd);
      } catch {
        /* transient — keep the last value */
      }
    };
    void loadCost();
    const id = setInterval(loadCost, REFRESH_MS);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <dl className="mt-3 space-y-1.5">
      <div className="flex items-center justify-between">
        <dt className="pixel-label">$ Sesión</dt>
        <dd className="font-mono text-xs font-bold text-coffee tabular-nums">
          {cost == null ? "…" : `$${cost.toFixed(4)}`}
        </dd>
      </div>
      <div className="flex items-center justify-between gap-2">
        <dt className="pixel-label shrink-0">Modelo</dt>
        <dd
          className="truncate font-mono text-xs font-bold text-coffee"
          title={model ?? undefined}
        >
          {model == null ? "…" : shortModel(model)}
        </dd>
      </div>
    </dl>
  );
}
