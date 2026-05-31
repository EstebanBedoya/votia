/** BFF proxy for GET /session/usage — the caller session's accumulated spend.
 *
 * Forwards the browser's (httponly, same-origin) session cookie so the backend
 * resolves the right session instead of minting a fresh, empty one. */

import { type NextRequest, NextResponse } from "next/server";

import { sessionUsage, UpstreamError } from "@/lib/api";

export async function GET(request: NextRequest) {
  try {
    return NextResponse.json(await sessionUsage(request.headers.get("cookie") ?? undefined));
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
