/** BFF proxy for GET /config — which models the system runs on. */

import { NextResponse } from "next/server";

import { config, UpstreamError } from "@/lib/api";

export async function GET() {
  try {
    return NextResponse.json(await config());
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
