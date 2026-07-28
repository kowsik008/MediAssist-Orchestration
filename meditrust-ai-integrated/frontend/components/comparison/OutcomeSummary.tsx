"use client";

import React from "react";
import { ComparisonScenario } from "@/lib/types";
import { Clock, ShieldCheck, Award, Zap } from "lucide-react";

interface OutcomeSummaryProps {
  scenario: ComparisonScenario;
}

export const OutcomeSummary: React.FC<OutcomeSummaryProps> = ({ scenario }) => {
  const cards = [
    { label: "Time Saved",          value: scenario.timeSaved,          sub: `${scenario.responseTimeBefore}ms → ${scenario.responseTimeAfter}ms`, icon: <Clock       className="w-4 h-4 text-[#1B5FA8]" />, bg: "bg-blue-50  border-blue-200" },
    { label: "Evidence Quality",    value: scenario.evidenceQuality,    sub: "Direct institutional source citations",                               icon: <ShieldCheck className="w-4 h-4 text-[#0E9F6E]" />, bg: "bg-green-50 border-green-200" },
    { label: "Quality Improvement", value: scenario.qualityImprovement, sub: "Zero unverified statements",                                          icon: <Award       className="w-4 h-4 text-violet-600" />, bg: "bg-violet-50 border-violet-200" },
    { label: "Safety Withholding",  value: scenario.unsafeWithheld ? "Correctly Enforced" : "Standard Guidance", sub: "Automated risk escalation active", icon: <Zap className="w-4 h-4 text-amber-600" />, bg: "bg-amber-50  border-amber-200" },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 my-6">
      {cards.map((c, idx) => (
        <div key={idx} className="clinical-panel p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">{c.label}</span>
            <div className={`p-1.5 rounded-lg border ${c.bg}`}>{c.icon}</div>
          </div>
          <div className="text-lg font-extrabold text-slate-900 mt-2">{c.value}</div>
          <div className="text-[11px] text-slate-400 mt-1">{c.sub}</div>
        </div>
      ))}
    </div>
  );
};
