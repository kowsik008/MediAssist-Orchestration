import {
  EvidenceSource,
  ComparisonScenario,
  AuditEvent,
  HealthcareRole,
  OrchestrationResponse,
  ServiceStatus,
} from "./types";

export interface StarterQueryItem {
  title: string;
  query: string;
  category: string;
  tagStyle: string;
}

/** Browser requests stay on the Next.js BFF; the BFF calls the integration gateway. */
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";

export async function fetchSources(): Promise<EvidenceSource[]> {
  try {
    const res = await fetch(`${API_BASE}/sources`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch sources:", err);
    return [];
  }
}

export async function fetchComparisons(): Promise<ComparisonScenario[]> {
  try {
    const res = await fetch(`${API_BASE}/comparisons`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch comparisons:", err);
    return [];
  }
}

export async function fetchAuditLogs(): Promise<AuditEvent[]> {
  try {
    const res = await fetch(`${API_BASE}/audit-logs`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch audit logs:", err);
    return [];
  }
}

export async function fetchServices(): Promise<ServiceStatus[]> {
  try {
    const res = await fetch(`${API_BASE}/services`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch services:", err);
    return [];
  }
}

export async function fetchStarterQueries(): Promise<StarterQueryItem[]> {
  try {
    const res = await fetch(`${API_BASE}/starter-queries`);
    if (!res.ok) return [];
    return await res.json();
  } catch (err) {
    console.error("Failed to fetch starter queries:", err);
    return [];
  }
}

export async function askAssistant(
  query: string,
  role: HealthcareRole,
): Promise<OrchestrationResponse> {
  const res = await fetch("/api/assistant", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, role }),
  });

  const payload = await res.json();
  if (!res.ok) {
    throw new Error(payload.error || "The governed assistant is unavailable.");
  }
  return payload as OrchestrationResponse;
}
