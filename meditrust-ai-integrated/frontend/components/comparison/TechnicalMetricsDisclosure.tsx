"use client";

import React, { useState } from "react";
import { ComparisonScenario } from "@/lib/types";
import { ChevronDown, ChevronUp, Cpu } from "lucide-react";

interface TechnicalMetricsDisclosureProps {
  scenario: ComparisonScenario;
}

export const TechnicalMetricsDisclosure: React.FC<TechnicalMetricsDisclosureProps> = ({ scenario }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="my-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 rounded-2xl bg-white border border-slate-200 shadow-sm text-xs font-semibold text-slate-600 hover:text-slate-900 hover:border-[#1B5FA8]/40 hover:bg-blue-50 transition-all"
      >
        <div className="flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-violet-600" />
          <span>Advanced Technical Metrics (Evaluators & System Architects)</span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isOpen && (
        <div className="mt-2 p-5 rounded-2xl bg-violet-50 border border-violet-200 space-y-4 animate-in fade-in">
          <div className="text-xs text-slate-500">
            Internal token optimization, cache performance, and model invocation details for technical evaluation only.
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm">
              <span className="text-slate-500">Context Token Reduction</span>
              <div className="text-lg font-extrabold text-slate-900">
                {scenario.tokensAfter} <span className="text-xs text-slate-400 font-normal">from {scenario.tokensBefore}</span>
              </div>
              <span className="text-[10px] text-[#0E9F6E] font-bold">
                -{Math.round((1 - scenario.tokensAfter / scenario.tokensBefore) * 100)}% prompt overhead
              </span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm">
              <span className="text-slate-500">Model Invocations Avoided</span>
              <div className="text-lg font-extrabold text-slate-900">{scenario.avoidedModelCalls} calls avoided</div>
              <span className="text-[10px] text-slate-400">Semantic cache shortcut</span>
            </div>

            <div className="p-3 rounded-xl bg-white border border-slate-200 space-y-1 shadow-sm">
              <span className="text-slate-500">Cache Hit Effectiveness</span>
              <div className="text-lg font-extrabold text-[#1B5FA8]">{scenario.cacheHitRate}</div>
              <span className="text-[10px] text-slate-400 font-mono">Headroom router active</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
