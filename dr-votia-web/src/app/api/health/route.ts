/** BFF proxy for GET /health — useful to confirm the backend is reachable. */

import { NextResponse } from "next/server";

import { UpstreamError, health } from "@/lib/api";

export async function GET() {
  try {
    return NextResponse.json(await health());
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
