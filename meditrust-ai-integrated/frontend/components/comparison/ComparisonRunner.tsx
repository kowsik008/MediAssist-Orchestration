"use client";

import React, { useState } from "react";
import { ComparisonScenario } from "@/lib/types";
import { OutcomeSummary } from "./OutcomeSummary";
import { AnswerComparison } from "./AnswerComparison";
import { ResponseTimeChart } from "./ResponseTimeChart";
import { TechnicalMetricsDisclosure } from "./TechnicalMetricsDisclosure";
import { GitCompare } from "lucide-react";

type WorkflowResult = {
  request_id: string;
  answer?: string;
  validation_status?: string;
  cache_hit?: boolean;
  metrics?: {
    latency_ms?: number;
    token_count_before?: number;
    token_count_after?: number;
    model_invocation_count?: number;
  };
};

export const ComparisonRunner: React.FC = () => {
  const [query, setQuery] = useState("");
  const [scenario, setScenario] = useState<ComparisonScenario | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runComparison = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/comparison", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), user_role: "doctor" }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.baseline || !payload.optimized) {
        throw new Error(payload.error || "Comparison failed.");
      }
      const baseline = payload.baseline as WorkflowResult;
      const optimized = payload.optimized as WorkflowResult;
      const before = baseline.metrics?.token_count_after ?? 0;
      const after = optimized.metrics?.token_count_after ?? 0;
      const reduction = before > 0 ? Math.max(0, ((before - after) / before) * 100) : 0;
      setScenario({
        id: optimized.request_id,
        title: "Live Comparison",
        query: query.trim(),
        standardResponse: baseline.answer ?? "No baseline answer returned.",
        governedResponse: optimized.answer ?? "No optimized answer returned.",
        timeSaved: `${Math.max(0, (baseline.metrics?.latency_ms ?? 0) - (optimized.metrics?.latency_ms ?? 0))} ms`,
        evidenceQuality: optimized.validation_status ?? "not measured",
        qualityImprovement: `${reduction.toFixed(1)}% token reduction`,
        unsafeWithheld: ["block", "escalate"].includes(optimized.validation_status ?? ""),
        responseTimeBefore: baseline.metrics?.latency_ms ?? 0,
        responseTimeAfter: optimized.metrics?.latency_ms ?? 0,
        tokensBefore: before,
        tokensAfter: after,
        avoidedModelCalls: Math.max(
          0,
          (baseline.metrics?.model_invocation_count ?? 0) -
            (optimized.metrics?.model_invocation_count ?? 0),
        ),
        cacheHitRate: optimized.cache_hit ? "Cache hit" : "Cache miss",
      });
    } catch (caught) {
      setScenario(null);
      setError(caught instanceof Error ? caught.message : "Comparison failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <label htmlFor="comparison-query" className="flex items-center gap-2 text-xs font-bold text-slate-600">
          <GitCompare className="w-4 h-4 text-[#1B5FA8]" />
          Live comparison query
        </label>
        <textarea
          id="comparison-query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="min-h-24 rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-[#1B5FA8]"
          placeholder="Enter a healthcare process question to run both workflows."
        />
        <button
          onClick={runComparison}
          disabled={loading || !query.trim()}
          className="self-start rounded-xl bg-[#1B5FA8] px-4 py-2 text-xs font-bold text-white disabled:opacity-50"
        >
          {loading ? "Running live workflows..." : "Run comparison"}
        </button>
        {error && <p className="text-xs text-rose-600">{error}</p>}
      </div>

      {scenario ? (
        <>
          <OutcomeSummary scenario={scenario} />
          <AnswerComparison scenario={scenario} />
          <ResponseTimeChart scenario={scenario} />
          <TechnicalMetricsDisclosure scenario={scenario} />
        </>
      ) : (
        <div className="text-center py-12 text-xs text-slate-400">
          No static scenarios are loaded. Submit a query to generate measured results.
        </div>
      )}
    </div>
  );
};
