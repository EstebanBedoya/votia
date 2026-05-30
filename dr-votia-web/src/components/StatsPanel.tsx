"use client";

/**
 * "MI COLECCIÓN DE DATOS" panel. Reuses the real radar scorecards (useRadar):
 * one tile per axis, showing the mean `solidez` across the scored candidates.
 */

import { StatTile } from "@/components/StatTile";
import { useRadar } from "@/hooks/useRadar";
import { EJES, EJE_ICON } from "@/lib/constants";

export function StatsPanel() {
  const { rows, cards, loading, error } = useRadar();

  // rows is one entry per axis (in EJES order) with a column per candidato id.
  const meanByAxis = rows.map((row) => {
    const values = cards
      .map((c) => Number(row[c.candidato] ?? 0))
      .filter((v) => v > 0);
    const mean = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
    return mean;
  });

  return (
    <aside className="pixel-panel flex h-full flex-col">
      <header className="border-b-4 border-coffee bg-surface-high px-3 py-2">
        <h2 className="font-display text-sm font-bold text-secondary">
          Mi colección de datos
        </h2>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto p-3 pixel-scroll">
        {loading && <p className="pixel-label">Cargando…</p>}
        {error && (
          <p className="pixel-label text-error" role="alert">
            {error}
          </p>
        )}
        {!loading && !error && cards.length === 0 && (
          <p className="pixel-label leading-relaxed">
            Sin scorecards. Corré <code>uv run dr-votia score</code>.
          </p>
        )}

        {cards.length > 0 && (
          <div className="grid grid-cols-2 gap-3">
            {EJES.map((eje, i) => (
              <StatTile
                key={eje.id}
                icon={EJE_ICON[eje.id]}
                label={eje.label}
                value={meanByAxis[i] ?? 0}
                href={`/eje/${eje.id}`}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
