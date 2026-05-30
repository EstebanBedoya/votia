"use client";

/**
 * Axis detail — drilled into from a "MI COLECCIÓN DE DATOS" tile. Shows every
 * scored candidate's EjeScore for this axis (solidez, supporting metrics, the
 * model's justification and the sources), ranked by solidez.
 */

import { notFound, useParams } from "next/navigation";
import Link from "next/link";

import { PixelIcon } from "@/components/PixelIcon";
import { PixelProgress } from "@/components/PixelProgress";
import { TitleBar } from "@/components/TitleBar";
import { useRadar } from "@/hooks/useRadar";
import { CANDIDATO_LABEL, EJES, EJE_ICON, EJE_LABEL } from "@/lib/constants";
import type { EjeScore, Eje } from "@/lib/types";

const VALID = new Set(EJES.map((e) => e.id));

function pct(x: number) {
  return `${Math.round(x * 100)}%`;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border-2 border-coffee bg-surface-low px-2 py-1.5 text-center">
      <div className="font-mono text-base font-bold text-secondary tabular-nums">{value}</div>
      <div className="pixel-label text-[10px] leading-tight text-on-surface-variant">{label}</div>
    </div>
  );
}

export default function EjeDetailPage() {
  const params = useParams<{ eje: string }>();
  const eje = params.eje as Eje;
  if (!VALID.has(eje)) notFound();

  const { cards, loading, error } = useRadar();

  // Pull this axis' score out of every candidate, ranked by solidez.
  const scored = cards
    .map((c) => ({ candidato: c.candidato, score: c.ejes.find((e) => e.eje === eje) }))
    .filter((x): x is { candidato: typeof x.candidato; score: EjeScore } => Boolean(x.score))
    .sort((a, b) => b.score.solidez - a.score.solidez);

  const mean =
    scored.length > 0
      ? scored.reduce((acc, s) => acc + s.score.solidez, 0) / scored.length
      : 0;

  return (
    <main className="mx-auto flex min-h-screen max-w-[1100px] flex-col gap-4 p-4 md:p-8">
      <TitleBar title={`Eje · ${EJE_LABEL[eje]}`} status="DETALLE" />

      {/* Hero */}
      <section className="pixel-panel flex items-center gap-4 p-5">
        <span className="grid h-16 w-16 shrink-0 place-items-center border-[3px] border-coffee bg-gold text-coffee pixel-shadow">
          <PixelIcon name={EJE_ICON[eje]} size={36} />
        </span>
        <div className="min-w-0 flex-1">
          <h2
            className="font-display text-2xl font-bold text-secondary"
            style={{ textShadow: "2px 2px 0 var(--color-gold)" }}
          >
            {EJE_LABEL[eje]}
          </h2>
          <p className="mt-1 text-sm text-on-surface-variant">
            Solidez promedio entre {scored.length} candidato{scored.length === 1 ? "" : "s"}{" "}
            evaluado{scored.length === 1 ? "" : "s"}.
          </p>
        </div>
        <div className="shrink-0 text-right">
          <div className="font-mono text-3xl font-bold text-tertiary tabular-nums">
            {mean.toFixed(1)}
          </div>
          <div className="pixel-label">/ 5.0</div>
        </div>
      </section>

      <div className="flex items-center justify-between gap-2">
        <Link
          href="/chat"
          className="inline-flex items-center gap-2 border-2 border-coffee bg-surface-low px-3 py-1.5 pixel-label transition-colors hover:bg-gold"
        >
          <PixelIcon name="back" size={16} /> Volver al chat
        </Link>
        <Link
          href="/radar"
          className="inline-flex items-center gap-2 border-2 border-coffee bg-surface-low px-3 py-1.5 pixel-label transition-colors hover:bg-gold"
        >
          Ver radar <PixelIcon name="chevron" size={16} />
        </Link>
      </div>

      {loading && <p className="pixel-label">Cargando scorecards…</p>}
      {error && (
        <p className="pixel-label text-error" role="alert">
          Error: {error}
        </p>
      )}
      {!loading && !error && scored.length === 0 && (
        <p className="text-sm text-on-surface-variant">
          No hay datos para este eje todavía. Corré{" "}
          <code className="border border-coffee bg-surface-low px-1 font-mono">
            uv run dr-votia score
          </code>
          .
        </p>
      )}

      {/* Per-candidate breakdown */}
      <div className="grid gap-4">
        {scored.map(({ candidato, score }, rank) => (
          <article key={candidato} className="pixel-panel p-5">
            <header className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="grid h-8 w-8 place-items-center border-2 border-coffee bg-secondary font-mono text-sm font-bold text-on-secondary">
                  {rank + 1}
                </span>
                <h3 className="font-display text-lg font-bold text-secondary">
                  {CANDIDATO_LABEL[candidato] ?? candidato}
                </h3>
              </div>
              <div className="flex items-center gap-3">
                <PixelProgress value={score.solidez} max={5} className="w-28" />
                <span className="font-mono text-xl font-bold text-tertiary tabular-nums">
                  {score.solidez.toFixed(1)}
                </span>
              </div>
            </header>

            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Metric label="Propuestas" value={score.volumen_propuestas} />
              <Metric label="Confianza" value={pct(score.confianza)} />
              <Metric label="Evidencia" value={pct(score.densidad_evidencia)} />
              <Metric label="Anclaje nac." value={pct(score.anclaje_nacional)} />
            </div>

            {score.justificacion && (
              <p className="mt-4 border-l-4 border-gold bg-surface-low px-3 py-2 text-sm leading-relaxed text-on-surface">
                {score.justificacion}
              </p>
            )}

            {score.fuentes.length > 0 && (
              <details className="mt-3 border-2 border-coffee bg-surface-low">
                <summary className="cursor-pointer select-none bg-surface-high px-2 py-1 pixel-label">
                  Fuentes ({score.fuentes.length})
                </summary>
                <ul className="space-y-1 px-3 py-2 font-mono text-[11px] leading-snug text-on-surface-variant">
                  {score.fuentes.map((f, i) => (
                    <li key={i} className="border-b border-outline-variant pb-1 last:border-0">
                      {f}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </article>
        ))}
      </div>
    </main>
  );
}
