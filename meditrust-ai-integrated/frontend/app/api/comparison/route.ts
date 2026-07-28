import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const requestSchema = z.object({
  query: z.string().min(1).max(4096),
  user_role: z.string().default("public"),
});

export async function POST(request: NextRequest) {
  const parsed = requestSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid comparison request." }, { status: 400 });
  }
  const gatewayUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  try {
    const invoke = (mode: "baseline" | "optimized") =>
      fetch(`${gatewayUrl}/api/v1/workflows/invoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...parsed.data, mode }),
        cache: "no-store",
        signal: AbortSignal.timeout(45_000),
      });
    const [baselineResponse, optimizedResponse] = await Promise.all([
      invoke("baseline"),
      invoke("optimized"),
    ]);
    return NextResponse.json({
      baseline: await baselineResponse.json(),
      optimized: await optimizedResponse.json(),
    });
  } catch {
    return NextResponse.json(
      { error: "Comparison workflow is temporarily unavailable." },
      { status: 503 },
    );
  }
}
