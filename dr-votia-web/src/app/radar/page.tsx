"use client";

/**
 * Radar page — pixel-art panel wrapping the themed radar. Candidate toggles are
 * rendered as pixel chips. Loads all scorecards and plots `solidez` per axis.
 */

import { useEffect, useState } from "react";

import { RadarChart } from "@/components/RadarChart";
import { TitleBar } from "@/components/TitleBar";
import { useRadar } from "@/hooks/useRadar";
import { CANDIDATOS } from "@/lib/constants";

export default function RadarPage() {
  const { cards, rows, loading, error } = useRadar();
  const [selected, setSelected] = useState<string[]>([]);

  // Default to whatever candidates the backend actually returned scorecards for.
  useEffect(() => {
    if (cards.length > 0 && selected.length === 0) {
      setSelected(cards.map((c) => c.candidato));
    }
  }, [cards, selected.length]);

  function toggle(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-[1200px] flex-col gap-4 p-4 md:p-8">
      <TitleBar title="Radar Comparativo — Solidez por Eje" status="ANÁLISIS" />

      <section className="pixel-panel flex-1 p-4 md:p-6">
        {loading && <p className="pixel-label">Cargando scorecards…</p>}
        {error && (
          <p className="pixel-label text-error" role="alert">
            Error: {error}
          </p>
        )}

        {!loading && !error && cards.length === 0 && (
          <p className="text-sm text-on-surface-variant">
            No hay scorecards calculados. Corré{" "}
            <code className="border border-coffee bg-surface-low px-1 font-mono">
              uv run dr-votia score
            </code>{" "}
            en el backend.
          </p>
        )}

        {cards.length > 0 && (
          <>
            <div className="mb-6 flex flex-wrap gap-2">
              {CANDIDATOS.filter((c) => cards.some((card) => card.candidato === c.id)).map(
                (c) => {
                  const on = selected.includes(c.id);
                  return (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => toggle(c.id)}
                      aria-pressed={on}
                      className={`border-2 border-coffee px-3 py-1.5 pixel-label transition-colors ${
                        on
                          ? "bg-gold text-coffee pixel-shadow"
                          : "bg-surface-low text-on-surface-variant"
                      }`}
                    >
                      {on ? "▣ " : "▢ "}
                      {c.label}
                    </button>
                  );
                },
              )}
            </div>

            <div className="border-[3px] border-coffee bg-surface-lowest p-4">
              <RadarChart rows={rows} candidatos={selected} />
            </div>
          </>
        )}
      </section>
    </main>
  );
}
