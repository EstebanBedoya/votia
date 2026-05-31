/**
 * BFF gate handler. Receives the access code the user typed, validates it
 * against the backend /auth endpoint, and — if valid — sets an httponly cookie
 * so all subsequent upstream requests are automatically authenticated.
 */

import { NextRequest, NextResponse } from "next/server";

import { UpstreamError, validateCode } from "@/lib/api";

const COOKIE_NAME = "votia_gate";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days

export async function POST(req: NextRequest) {
  let code: string;
  try {
    const body = (await req.json()) as { code?: unknown };
    if (typeof body.code !== "string" || !body.code.trim()) {
      return NextResponse.json({ error: "Código requerido." }, { status: 400 });
    }
    code = body.code.trim();
  } catch {
    return NextResponse.json({ error: "Solicitud inválida." }, { status: 400 });
  }

  try {
    await validateCode(code);
  } catch (err) {
    if (err instanceof UpstreamError && err.status === 401) {
      return NextResponse.json({ error: "Código incorrecto." }, { status: 401 });
    }
    return NextResponse.json(
      { error: "No se pudo conectar con el servidor." },
      { status: 502 },
    );
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(COOKIE_NAME, code, {
    httpOnly: true,
    sameSite: "lax",
    maxAge: COOKIE_MAX_AGE,
    path: "/",
  });
  return res;
}
