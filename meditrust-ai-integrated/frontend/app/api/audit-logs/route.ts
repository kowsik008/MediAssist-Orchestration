import { NextResponse } from "next/server";

type AuditRecord = {
  audit_id: string;
  request_id: string;
  risk_level: string;
  input_decision: string;
  output_decision?: string | null;
  created_at: string;
};

export async function GET() {
  const gatewayUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${gatewayUrl}/api/v1/audit/recent?window_hours=720&limit=100`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      return NextResponse.json({ error: "Audit service unavailable." }, { status: response.status });
    }
    const records = (await response.json()) as AuditRecord[];
    return NextResponse.json(
      records.map((record) => {
        const decision = record.output_decision || record.input_decision;
        const escalated = decision === "escalate" || decision === "block";
        return {
          id: record.audit_id,
          timestamp: record.created_at,
          requestId: record.request_id,
          riskCategory:
            record.risk_level === "high" ? "High" :
            record.risk_level === "medium" ? "Medium" : "Low",
          decision:
            decision === "block" || decision === "escalate"
              ? "Withheld & Referred"
              : decision === "clarify" || decision === "regenerate"
                ? "Clarified"
                : "Passed",
          humanReviewStatus: escalated ? "Escalated" : "Approved",
        };
      }),
    );
  } catch {
    return NextResponse.json({ error: "Audit service unavailable." }, { status: 503 });
  }
}
