/** BFF proxy for GET /usage — OpenRouter credit budget (ENERGÍA gauge). */

import { NextResponse } from "next/server";

import { UpstreamError, usage } from "@/lib/api";

export async function GET() {
  try {
    return NextResponse.json(await usage());
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
