/**
 * BFF proxy for POST /chat. Relays the session cookie both ways: forwards the
 * browser's Cookie header to FastAPI, and re-mirrors FastAPI's Set-Cookie back to
 * the browser. Same-origin + httponly means the browser handles the cookie itself.
 */

import { NextResponse } from "next/server";

import { UpstreamError, chat } from "@/lib/api";
import type { ChatRequest } from "@/lib/types";

export async function POST(req: Request) {
  let body: ChatRequest;
  try {
    body = (await req.json()) as ChatRequest;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const cookie = req.headers.get("cookie") ?? undefined;

  try {
    const { data, setCookie } = await chat(body, cookie);
    const res = NextResponse.json(data);
    if (setCookie) res.headers.set("set-cookie", setCookie);
    return res;
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
