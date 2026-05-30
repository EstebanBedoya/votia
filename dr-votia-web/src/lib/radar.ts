/**
 * Reshape scorecards for recharts. The API gives one RadarResponse per candidate,
 * each with a list of per-axis metrics. A recharts RadarChart wants the transpose:
 * one row per axis, with a column per candidate holding that axis' `solidez` (1–5).
 * We walk the axes in a fixed order (EJES) so the chart shape is stable regardless
 * of backend ordering.
 */

import { EJES, EJE_LABEL } from "@/lib/constants";
import type { RadarResponse } from "@/lib/types";

/** One row of the recharts dataset: an axis label plus one solidez per candidate. */
export interface RadarRow {
  eje: string;
  /** candidato id -> solidez on this axis (0 when missing). */
  [candidato: string]: string | number;
}

/**
 * Build the recharts dataset from a set of scorecards.
 * Returns 6 rows (one per axis) with a numeric column for each given candidate.
 */
export function toRadarData(cards: RadarResponse[]): RadarRow[] {
  const byCandidate = new Map<string, Map<string, number>>();
  for (const card of cards) {
    const axes = new Map(card.ejes.map((e) => [e.eje, e.solidez]));
    byCandidate.set(card.candidato, axes);
  }

  return EJES.map(({ id }) => {
    const row: RadarRow = { eje: EJE_LABEL[id] ?? id };
    for (const [candidato, axes] of byCandidate) {
      row[candidato] = axes.get(id) ?? 0;
    }
    return row;
  });
}

/** The candidate ids present in a set of cards, preserving input order. */
export function candidatosEnCards(cards: RadarResponse[]): string[] {
  return cards.map((c) => c.candidato);
}
