import { NextResponse } from "next/server";

type SourceRecord = {
  document_id: string;
  title: string;
  publisher: string;
  source_type: "public_guideline" | "synthetic_sop";
  version_date: string;
  status: "active" | "superseded" | "expired" | "draft";
  access_roles: string[];
  synthetic: boolean;
  content: string;
};

const roleLabels: Record<string, string> = {
  doctor: "Doctor",
  nurse: "Nurse",
  pharmacist: "Pharmacist",
  compliance_officer: "Compliance Officer",
  administrator: "Administrator",
};

export async function GET() {
  const gatewayUrl = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await fetch(`${gatewayUrl}/api/v1/sources`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) {
      return NextResponse.json({ error: "Knowledge catalog unavailable." }, { status: response.status });
    }
    const records = (await response.json()) as SourceRecord[];
    return NextResponse.json(
      records.map((source) => ({
        id: source.document_id,
        title: source.title,
        publisher: source.publisher,
        publishDate: source.version_date,
        version: source.version_date,
        sourceType: source.synthetic ? "Synthetic Demonstration" : "Clinical Guidance",
        status:
          source.synthetic ? "Demonstration only" :
          source.status === "active" ? "Current" :
          source.status === "superseded" ? "Superseded" : "Expired",
        isSynthetic: source.synthetic,
        accessRole:
          source.access_roles.includes("public") || source.access_roles.length !== 1
            ? "All Users"
            : roleLabels[source.access_roles[0]] ?? "All Users",
        excerpt: source.content.replace(/^#+\s.*$/gm, "").trim().slice(0, 320),
        fullContent: source.content,
        citationCount: 0,
        thumbnailUrl: "",
        publisherMark: source.publisher,
      })),
    );
  } catch {
    return NextResponse.json({ error: "Knowledge catalog unavailable." }, { status: 503 });
  }
}
