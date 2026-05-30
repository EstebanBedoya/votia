/**
 * Server-side API client. Used ONLY by the BFF route handlers (src/app/api/**),
 * never imported into client components — that keeps API_BASE_URL off the browser.
 *
 * Session handling: the backend tracks conversation memory with an httponly
 * cookie (`dr_session`). The browser cannot read it, so we relay it through the
 * proxy: `chat` forwards the incoming Cookie header to FastAPI and returns the
 * Set-Cookie it sends back, so the route handler can re-mirror it to the browser.
 */

import "server-only";

import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  RadarResponse,
  UsageResponse,
} from "@/lib/types";

const BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

/** Thrown when the upstream FastAPI responds with a non-2xx status. */
export class UpstreamError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "UpstreamError";
  }
}

async function call(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${BASE}${path}`, {
      ...init,
      headers: { "content-type": "application/json", ...init?.headers },
      // Backend responses are request-specific; never cache at the fetch layer.
      cache: "no-store",
    });
  } catch {
    throw new UpstreamError(502, `Backend unreachable at ${BASE}`);
  }
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new UpstreamError(res.status, detail || res.statusText);
  }
  return (await res.json()) as T;
}

/** A chat result plus the raw Set-Cookie the backend wants the browser to store. */
export interface ChatResult {
  data: ChatResponse;
  setCookie: string | null;
}

/** POST /chat — relays the session cookie in both directions. */
export async function chat(body: ChatRequest, cookie?: string): Promise<ChatResult> {
  const headers: Record<string, string> = {};
  if (cookie) headers["cookie"] = cookie;
  const res = await call("/chat", {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const data = await json<ChatResponse>(res);
  return { data, setCookie: res.headers.get("set-cookie") };
}

/** GET /radar — all candidate scorecards. */
export async function radarAll(): Promise<RadarResponse[]> {
  return json<RadarResponse[]>(await call("/radar"));
}

/** GET /radar/{candidato} — one scorecard (404 if not yet scored). */
export async function radar(candidato: string): Promise<RadarResponse> {
  return json<RadarResponse>(await call(`/radar/${encodeURIComponent(candidato)}`));
}

/** GET /health */
export async function health(): Promise<HealthResponse> {
  return json<HealthResponse>(await call("/health"));
}

/** GET /usage — OpenRouter credit budget. */
export async function usage(): Promise<UsageResponse> {
  return json<UsageResponse>(await call("/usage"));
}
