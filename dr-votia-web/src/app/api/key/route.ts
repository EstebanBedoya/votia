/** BFF proxy for GET /key — OpenRouter key spending limit (ENERGÍA gauge). */

import { NextResponse } from "next/server";

import { key, UpstreamError } from "@/lib/api";

export async function GET() {
  try {
    return NextResponse.json(await key());
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
