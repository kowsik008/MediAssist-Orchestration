import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const requestSchema = z.object({
  query: z.string().min(2).max(2000),
  role: z.string().default("public"),
  top_k: z.number().int().min(1).max(20).default(5),
  status: z.string().default("active"),
  source_type: z.string().optional(),
});

export async function POST(request: NextRequest) {
  const parsed = requestSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid evidence request." }, { status: 400 });
  }
  const gatewayUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${gatewayUrl}/api/v1/evidence`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed.data),
      cache: "no-store",
      signal: AbortSignal.timeout(20_000),
    });
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json(
      { error: "Evidence retrieval is temporarily unavailable." },
      { status: 503 },
    );
  }
}
