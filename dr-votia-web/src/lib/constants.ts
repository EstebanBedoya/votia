/**
 * Display metadata for the domain enums. The backend speaks lowercase slugs
 * (matching domain/models.py); the UI needs readable labels and a fixed order.
 */

import type { PixelIconName } from "@/components/PixelIcon";
import type { Candidato, Eje } from "@/lib/types";

export interface CandidatoMeta {
  id: Candidato;
  label: string;
}

export interface EjeMeta {
  id: Eje;
  label: string;
}

/** The five evaluable candidates (excludes the `nacional` pseudo-author). */
export const CANDIDATOS: CandidatoMeta[] = [
  { id: "cepeda", label: "Iván Cepeda" },
  { id: "valencia", label: "Paloma Valencia" },
  { id: "fajardo", label: "Sergio Fajardo" },
  { id: "lopez", label: "Claudia López" },
  { id: "espriella", label: "Abelardo de la Espriella" },
];

/** The 6 thematic axes of the radar, in fixed display order (Docs/plan.md §5). */
export const EJES: EjeMeta[] = [
  { id: "seguridad", label: "Seguridad" },
  { id: "economia", label: "Economía y empleo" },
  { id: "salud", label: "Salud" },
  { id: "educacion", label: "Educación" },
  { id: "anticorrupcion", label: "Anticorrupción" },
  { id: "medioambiente", label: "Medio ambiente" },
];

/** Pixel-icon glyph per axis (see PixelIcon). */
export const EJE_ICON: Record<Eje, PixelIconName> = {
  seguridad: "shield",
  economia: "coin",
  salud: "cross",
  educacion: "book",
  anticorrupcion: "scales",
  medioambiente: "leaf",
};

export const CANDIDATO_LABEL: Record<string, string> = Object.fromEntries(
  CANDIDATOS.map((c) => [c.id, c.label]),
);

export const EJE_LABEL: Record<string, string> = Object.fromEntries(
  EJES.map((e) => [e.id, e.label]),
);
