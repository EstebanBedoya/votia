/** BFF proxy for GET /radar — all scorecards. */

import { NextResponse } from "next/server";

import { UpstreamError, radarAll } from "@/lib/api";

export async function GET() {
  try {
    return NextResponse.json(await radarAll());
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
