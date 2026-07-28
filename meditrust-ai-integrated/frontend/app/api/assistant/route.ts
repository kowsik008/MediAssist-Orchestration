import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

const requestSchema = z.object({
  query: z.string().min(1).max(4096),
  role: z.enum([
    "Doctor",
    "Nurse",
    "Pharmacist",
    "Compliance Officer",
    "Administrator",
  ]),
});

const roleMap = {
  Doctor: "doctor",
  Nurse: "nurse",
  Pharmacist: "pharmacist",
  "Compliance Officer": "compliance_officer",
  Administrator: "administrator",
} as const;

const gatewayUrl =
  process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  const parsed = requestSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json(
      { error: "Invalid assistant request", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  try {
    const response = await fetch(
      `${gatewayUrl}/api/v1/workflows/invoke`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: parsed.data.query,
          user_role: roleMap[parsed.data.role],
          mode: "optimized",
          top_k: 5,
          status_filter: "active",
        }),
        cache: "no-store",
        signal: AbortSignal.timeout(30_000),
      },
    );

    const payload = await response.json();
    if (!response.ok) {
      return NextResponse.json(
        {
          error: "Orchestration service rejected the request",
          detail: payload,
        },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch (error) {
    console.error("Assistant BFF request failed:", error);
    return NextResponse.json(
      {
        error: "The governed assistant is temporarily unavailable.",
        final_status: "dependency_unavailable",
      },
      { status: 503 },
    );
  }
}
