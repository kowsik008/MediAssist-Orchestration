export type HealthcareRole =
  | "Doctor"
  | "Nurse"
  | "Pharmacist"
  | "Compliance Officer"
  | "Administrator";

export type SourceFreshness =
  | "Current"
  | "Superseded"
  | "Expired"
  | "Demonstration only";

export type PlainProgressStep =
  | "Checking your request"
  | "Reviewing safety and scope"
  | "Clarifying the search"
  | "Searching trusted sources"
  | "Reviewing supporting evidence"
  | "Preparing a concise summary"
  | "Verifying citations and safety";

export interface Citation {
  id: string;
  sourceId: string;
  title: string;
  publisher: string;
  versionDate: string;
  excerpt: string;
  section: string;
  isSynthetic?: boolean;
}

export interface CautionItem {
  id: string;
  statementReference: string;
  text: string;
  severity: "low" | "medium" | "high";
}

export interface AssistantMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  userRole?: HealthcareRole;
  progressSteps?: PlainProgressStep[];
  isComplete?: boolean;
  citations?: Citation[];
  cautions?: CautionItem[];
  isWithheld?: boolean;
  isUnavailable?: boolean;
  withheldReason?: string;
  badges?: string[]; // e.g. ["Evidence reviewed", "Answer verified"]
}

export interface OrchestrationCitation {
  document_id?: string;
  chunk_id?: string;
  title?: string;
  publisher?: string;
  version_date?: string;
  section?: string;
  synthetic?: boolean;
  is_synthetic?: boolean;
}

export interface OrchestrationResponse {
  request_id: string;
  answer: string;
  source_ids: string[];
  citations: OrchestrationCitation[];
  warnings: string[];
  negative_statements: string[];
  escalation_text?: string | null;
  evidence_status?: string | null;
  cache_hit: boolean;
  final_status: string;
  metrics: {
    latency_ms: number;
    provider_latency_ms: number;
    model_invocation_count: number;
    token_count_before: number;
    token_count_after: number;
  };
}

export interface EvidenceSource {
  id: string;
  title: string;
  publisher: string;
  publishDate: string;
  version: string;
  sourceType: "Clinical Guidance" | "Policy Document" | "Formulary Standard" | "Synthetic Demonstration";
  status: SourceFreshness;
  isSynthetic: boolean;
  accessRole: HealthcareRole | "All Users";
  excerpt: string;
  fullContent: string;
  citationCount: number;
  thumbnailUrl: string;
  publisherMark?: string;
}

export interface ComparisonScenario {
  id: string;
  title: string;
  query: string;
  standardResponse: string;
  governedResponse: string;
  timeSaved: string;
  evidenceQuality: string;
  qualityImprovement: string;
  unsafeWithheld: boolean;
  responseTimeBefore: number; // in ms
  responseTimeAfter: number; // in ms
  tokensBefore: number;
  tokensAfter: number;
  avoidedModelCalls: number;
  cacheHitRate: string;
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  requestId: string;
  riskCategory: "Low" | "Medium" | "High" | "Restricted";
  decision: "Passed" | "Withheld & Referred" | "Clarified";
  humanReviewStatus: "Pending Review" | "Approved" | "Escalated";
}

export interface ServiceStatus {
  id: string;
  name: string;
  displayName: string;
  status: "Operational" | "Degraded" | "Unavailable";
  plainLanguageImpact: "Fully operational" | "Vector fallback active" | "Evidence-only mode" | "Retrieval unavailable";
  latencyMs: number;
}
