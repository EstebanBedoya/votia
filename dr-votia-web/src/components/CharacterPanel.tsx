/**
 * Right column: the Guacamayo character with a greeting, a visible Colombian
 * flag, and a "GUACAMAYO AI" status card with an XP/level bar.
 */

import Image from "next/image";

import { EnergyBar } from "@/components/EnergyBar";
import { SessionStats } from "@/components/SessionStats";
import { artUrl } from "@/lib/assets";

export interface CharacterPanelProps {
  /** Short greeting shown in the speech bubble. */
  greeting?: string;
}

export function CharacterPanel({ greeting = "¡Datos a la mano!" }: CharacterPanelProps) {
  return (
    <aside className="flex h-full flex-col items-center gap-4">
      {/* Greeting + flag row */}
      <div className="flex w-full items-start justify-between gap-2">
        <div className="relative border-[3px] border-coffee bg-surface-lowest px-3 py-1.5 pixel-shadow">
          <span className="font-mono text-xs font-bold text-coffee">{greeting}</span>
        </div>
        <Image
          src={artUrl("flag.png")}
          alt="Bandera de Colombia"
          width={104}
          height={76}
          className="pixelated w-16 shrink-0 drop-shadow-[3px_3px_0_rgba(0,0,0,0.25)]"
        />
      </div>

      {/* Parrot */}
      <Image
        src={artUrl("guacamayo.png")}
        alt="Guacamayo, el asistente"
        width={224}
        height={296}
        priority
        className="pixelated w-full max-w-[200px] drop-shadow-[4px_4px_0_rgba(0,0,0,0.25)]"
      />

      {/* Status card */}
      <div className="pixel-panel mt-auto w-full p-3">
        <h3 className="font-display text-sm font-bold text-secondary">Guacamayo AI</h3>
        <p className="pixel-label mt-0.5 text-on-surface-variant">Tu guía cultural</p>
        <div className="mt-3">
          <EnergyBar />
        </div>
        <SessionStats />
      </div>
    </aside>
  );
}
