"use client";

import React from "react";
import { ComparisonScenario } from "@/lib/types";
import { ShieldCheck, AlertCircle } from "lucide-react";

interface AnswerComparisonProps {
  scenario: ComparisonScenario;
}

export const AnswerComparison: React.FC<AnswerComparisonProps> = ({ scenario }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 my-6">
      {/* Standard Baseline */}
      <div className="clinical-panel p-5 space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Standard Un-Governed Baseline</span>
          <span className="text-[11px] text-slate-400 font-mono bg-slate-100 px-2 py-0.5 rounded border border-slate-200">Generic LLM</span>
        </div>
        <div className="text-xs text-slate-600 leading-relaxed whitespace-pre-wrap p-3 rounded-xl bg-slate-50 border border-slate-200">
          {scenario.standardResponse}
        </div>
        <div className="text-[11px] text-slate-400 flex items-center gap-1 pt-1">
          <AlertCircle className="w-3.5 h-3.5 text-slate-400" />
          Lacks exact section citations and safety guardrails.
        </div>
      </div>

      {/* Governed Output */}
      <div className="clinical-panel-green p-5 space-y-3 rounded-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-green-200">
          <span className="text-xs font-bold uppercase tracking-wider text-[#047857] flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#0E9F6E]" />
            MediTrust Governed Output
          </span>
          <span className="text-[11px] text-[#047857] font-bold px-2 py-0.5 rounded bg-green-100 border border-green-200">
            Citation-Grounded
          </span>
        </div>
        <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap p-3 rounded-xl bg-white border border-green-200">
          {scenario.governedResponse}
        </div>
        <div className="text-[11px] text-[#0E9F6E] flex items-center gap-1 pt-1 font-semibold">
          <ShieldCheck className="w-3.5 h-3.5" />
          Fully verified with section references and clinical cautions.
        </div>
      </div>
    </div>
  );
};
