/**
 * Wire-format types — a 1:1 mirror of the FastAPI Pydantic schemas
 * (dr-votia/src/dr_votia/entrypoints/web/schemas.py) and the domain enums
 * (dr-votia/src/dr_votia/domain/models.py). Kept as string-literal unions
 * (not TS enums) so they match the JSON sent over the wire exactly.
 */

/** `nacional` is the baseline-data pseudo-author, never a real candidate. */
export type Candidato = "fajardo" | "lopez" | "cepeda" | "valencia" | "espriella" | "nacional";

/** `general` is a catch-all topic, excluded from the radar. */
export type Tema =
  | "seguridad"
  | "economia"
  | "salud"
  | "educacion"
  | "anticorrupcion"
  | "medioambiente"
  | "general";

export type Tipo = "propuesta" | "dato_historico" | "estadistica_nacional";

/** The six radar axes are exactly the Tema values minus `general`. */
export type Eje = Exclude<Tema, "general">;

/** POST /chat — request body. Mirrors ChatRequest. */
export interface ChatRequest {
  pregunta: string;
  /** 1..20, backend default 5. */
  k?: number;
  candidato?: Candidato;
  tema?: Tema;
  tipo?: Tipo;
}

/** One retrieved chunk backing an answer. Mirrors SourceDTO. */
export interface Source {
  fuente: string;
  tipo: Tipo;
  /** Vector similarity of the chunk to the query. */
  similarity: number;
  content: string;
  candidato?: Candidato | null;
  tema?: Tema | null;
  subtema?: string | null;
  pagina?: number | null;
  año?: number | null;
}

/** POST /chat — response body. Mirrors ChatResponse. */
export interface ChatResponse {
  respuesta: string;
  fuentes: Source[];
  session_id: string | null;
}

/** One axis of a candidate's scorecard. Mirrors EjeScoreDTO. */
export interface EjeScore {
  eje: Tema;
  volumen_propuestas: number;
  /** 1..5 — the value plotted on the radar. */
  solidez: number;
  solidez_std: number;
  solidez_runs: number[];
  confianza: number;
  densidad_evidencia: number;
  anclaje_nacional: number;
  coherencia_gestion: number | null;
  justificacion: string;
  fuentes: string[];
}

/** GET /radar/{candidato} — response body. Mirrors RadarResponse. */
export interface RadarResponse {
  candidato: Candidato;
  /** 0..6 — axes with at least one proposal. */
  cobertura: number;
  /** Herfindahl index over proposal volume per axis. */
  concentracion_hhi: number;
  presencia_historica: number;
  computed_at: string;
  ejes: EjeScore[];
}

/** GET /health */
export interface HealthResponse {
  status: string;
}

/** GET /usage — OpenRouter credit budget for the "ENERGÍA" gauge. */
export interface UsageResponse {
  total: number;
  used: number;
  remaining: number;
  /** Remaining as a percentage, or null when the account has no credit cap. */
  pct: number | null;
}

/** Shape returned to the browser when an upstream call fails. */
export interface ApiError {
  error: string;
}
