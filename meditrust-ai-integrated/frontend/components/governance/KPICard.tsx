"use client";

import React, { useEffect, useState } from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { ShieldCheck, Activity, Cpu, Database, Ban, EyeOff } from "lucide-react";

type Metrics = {
  guardrail_stats?: {
    total_requests?: number;
    blocked?: number;
    escalated?: number;
    redacted?: number;
  };
  token_stats?: {
    total_tokens_before?: number;
    total_tokens_after?: number;
  };
  total_llm_calls?: number;
  citation_validity_pct?: number | null;
};

export const KPICard: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    fetch("/api/metrics?window_hours=720", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then(setMetrics)
      .catch(() => setMetrics(null));
  }, []);

  const guards = metrics?.guardrail_stats;
  const before = metrics?.token_stats?.total_tokens_before ?? 0;
  const after = metrics?.token_stats?.total_tokens_after ?? 0;
  const reduction = before > 0 ? `${Math.max(0, ((before - after) / before) * 100).toFixed(1)}%` : "Not measured";
  const value = (number?: number | null, suffix = "") =>
    number === null || number === undefined ? "Not measured" : `${number}${suffix}`;
  const kpis = [
    { title: "Governed Requests", value: value(guards?.total_requests), subtitle: "Last 30 Days", icon: <Database className="w-4 h-4 text-[#6a5fc1]" /> },
    { title: "Citation Validity", value: value(metrics?.citation_validity_pct, "%"), subtitle: "Validated References", icon: <ShieldCheck className="w-4 h-4 text-[#23865f]" /> },
    { title: "Blocked Requests", value: value(guards?.blocked), subtitle: "Guardrail Decisions", icon: <Ban className="w-4 h-4 text-[#b5414c]" /> },
    { title: "Escalations", value: value(guards?.escalated), subtitle: "Human Review Required", icon: <Activity className="w-4 h-4 text-[#a66a00]" /> },
    { title: "Redacted Inputs", value: value(guards?.redacted), subtitle: "Sensitive Text Protected", icon: <EyeOff className="w-4 h-4 text-[#23865f]" /> },
    { title: "Model Calls", value: value(metrics?.total_llm_calls), subtitle: "Recorded Invocations", icon: <Cpu className="w-4 h-4 text-[#716a7d]" /> },
    { title: "Token Reduction", value: reduction, subtitle: "Measured Optimization", icon: <Cpu className="w-4 h-4 text-[#1B5FA8]" /> },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4 my-6">
      {kpis.map((kpi) => (
        <SurfaceCard key={kpi.title} variant="transactional" className="p-4 flex flex-col justify-between space-y-2 border-[#e5e7eb]">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[#716a7d] font-semibold">{kpi.title}</span>
            <div className="p-1.5 rounded-lg border bg-slate-50 border-slate-200">{kpi.icon}</div>
          </div>
          <div className="text-2xl font-bold text-[#1f1633]">{kpi.value}</div>
          <div className="text-[11px] text-[#23865f] font-bold">{kpi.subtitle}</div>
        </SurfaceCard>
      ))}
    </div>
  );
};
