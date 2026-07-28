import { NextResponse } from "next/server";

export async function GET() {
  const gatewayUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${gatewayUrl}/api/v1/metrics`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status });
  } catch {
    return NextResponse.json(
      { error: "Metrics are temporarily unavailable." },
      { status: 503 },
    );
  }
}
