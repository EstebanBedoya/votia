/** Collapsible pixel-art panel listing the sources backing an answer. */

import { CANDIDATO_LABEL } from "@/lib/constants";
import type { Source } from "@/lib/types";

export function Sources({ fuentes }: { fuentes: Source[] }) {
  if (fuentes.length === 0) return null;
  return (
    <details className="mt-3 border-2 border-coffee bg-surface-low">
      <summary className="cursor-pointer select-none bg-surface-high px-2 py-1 pixel-label">
        Fuentes ({fuentes.length})
      </summary>
      <ul className="space-y-1 px-3 py-2 font-mono text-[11px] leading-snug text-on-surface-variant">
        {fuentes.map((s, i) => (
          <li key={i} className="border-b border-outline-variant pb-1 last:border-0">
            <strong className="text-coffee">{s.fuente}</strong>
            {s.pagina != null && <> · pág. {s.pagina}</>}
            {s.candidato && <> · {CANDIDATO_LABEL[s.candidato] ?? s.candidato}</>}
            {s.tema && <> · {s.tema}</>} · {s.tipo} · sim {s.similarity.toFixed(3)}
          </li>
        ))}
      </ul>
    </details>
  );
}
