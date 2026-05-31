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

import { cookies } from "next/headers";

import type {
  ChatRequest,
  ChatResponse,
  ConfigResponse,
  HealthResponse,
  KeyResponse,
  RadarResponse,
  SessionUsageResponse,
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
  // Inject the access code from the gate cookie so every upstream request is
  // automatically authenticated — callers don't need to think about it.
  const cookieStore = await cookies();
  const gate = cookieStore.get("votia_gate")?.value;
  const gateHeader: Record<string, string> = gate ? { "x-access-code": gate } : {};

  try {
    return await fetch(`${BASE}${path}`, {
      ...init,
      headers: {
        "content-type": "application/json",
        ...gateHeader,
        ...init?.headers,
      },
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

/** GET /usage — OpenRouter account credit budget (lifetime). */
export async function usage(): Promise<UsageResponse> {
  return json<UsageResponse>(await call("/usage"));
}

/** GET /key — OpenRouter key spending limit + burned (ENERGÍA gauge). */
export async function key(): Promise<KeyResponse> {
  return json<KeyResponse>(await call("/key"));
}

/** GET /config — which models the system runs on. */
export async function config(): Promise<ConfigResponse> {
  return json<ConfigResponse>(await call("/config"));
}

/**
 * GET /session/usage — accumulated spend for the caller's session.
 * Relays the browser's session cookie so the backend resolves the right session
 * (without it, the backend would mint a fresh, empty one).
 */
export async function sessionUsage(cookie?: string): Promise<SessionUsageResponse> {
  const headers: Record<string, string> = {};
  if (cookie) headers["cookie"] = cookie;
  return json<SessionUsageResponse>(await call("/session/usage", { headers }));
}

/**
 * GET /auth — validate an access code without spending LLM tokens.
 * Used by the gate route handler to check the code the user typed.
 * Does NOT go through `call()` — we pass the code directly, not from cookie.
 */
export async function validateCode(code: string): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/auth`, {
      headers: { "content-type": "application/json", "x-access-code": code },
      cache: "no-store",
    });
  } catch {
    throw new UpstreamError(502, `Backend unreachable at ${BASE}`);
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new UpstreamError(res.status, detail || res.statusText);
  }
}
