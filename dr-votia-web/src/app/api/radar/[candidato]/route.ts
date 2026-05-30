/** BFF proxy for GET /radar/{candidato} — one scorecard. */

import { NextResponse } from "next/server";

import { UpstreamError, radar } from "@/lib/api";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ candidato: string }> },
) {
  const { candidato } = await params;
  try {
    return NextResponse.json(await radar(candidato));
  } catch (err) {
    if (err instanceof UpstreamError) {
      return NextResponse.json({ error: err.message }, { status: err.status });
    }
    return NextResponse.json({ error: "Unexpected error" }, { status: 500 });
  }
}
