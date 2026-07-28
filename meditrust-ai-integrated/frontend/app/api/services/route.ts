import { NextResponse } from "next/server";

export async function GET() {
  const gatewayUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${gatewayUrl}/api/v1/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
    if (!response.ok) {
      return NextResponse.json({ error: "Health service unavailable." }, { status: response.status });
    }
    const payload = await response.json();
    return NextResponse.json(
      (payload.dependencies ?? []).map(
        (dependency: { name: string; status: string; latency_ms?: number }) => ({
          id: dependency.name,
          name: dependency.name,
          displayName: dependency.name
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase()),
          status:
            dependency.status === "ok"
              ? "Operational"
              : dependency.status === "degraded"
                ? "Degraded"
                : "Unavailable",
          plainLanguageImpact:
            dependency.status === "ok"
              ? "Fully operational"
              : dependency.name === "knowledge_service" && dependency.status === "degraded"
                ? "Vector fallback active"
                : dependency.name === "knowledge_service"
                  ? "Retrieval unavailable"
                : "Evidence-only mode",
          latencyMs: dependency.latency_ms ?? 0,
        }),
      ),
    );
  } catch {
    return NextResponse.json({ error: "Health service unavailable." }, { status: 503 });
  }
}
