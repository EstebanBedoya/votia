"use client";

/**
 * Fetches all scorecards from the BFF (/api/radar) and reshapes them for recharts.
 * Returns both the raw cards and the chart-ready rows so the page can do either.
 */

import { useEffect, useState } from "react";

import { toRadarData, type RadarRow } from "@/lib/radar";
import type { RadarResponse } from "@/lib/types";

export interface UseRadar {
  cards: RadarResponse[];
  rows: RadarRow[];
  loading: boolean;
  error: string | null;
  reload: () => void;
}

export function useRadar(): UseRadar {
  const [cards, setCards] = useState<RadarResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetch("/api/radar")
      .then(async (res) => {
        const data = await res.json();
        if (!res.ok) throw new Error(data?.error ?? `Request failed (${res.status})`);
        if (!cancelled) setCards(data as RadarResponse[]);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unexpected error");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [tick]);

  return {
    cards,
    rows: toRadarData(cards),
    loading,
    error,
    reload: () => setTick((t) => t + 1),
  };
}
