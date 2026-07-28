"use client";

import React from "react";
import { ArrowRight, ShieldCheck, Database, Cpu, Layers } from "lucide-react";

export const FallbackPath: React.FC = () => {
  return (
    <div className="clinical-panel p-6 my-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#1B5FA8]" />
            Service Topology & Fallback Degradation Route
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">Automated failover sequence during telemetry or primary provider disruption.</p>
        </div>
        <span className="text-xs text-[#0E9F6E] font-bold bg-green-50 border border-green-200 px-2.5 py-0.5 rounded-full">Resilient Pipeline</span>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
        <div className="flex flex-col items-center p-3 rounded-xl bg-white border border-blue-200 shadow-sm text-center w-full md:w-auto min-w-[110px]">
          <ShieldCheck className="w-5 h-5 text-[#1B5FA8] mb-1" />
          <span className="font-bold text-slate-800">API Gateway</span>
          <span className="text-[10px] text-slate-400">Request Routing</span>
        </div>

        <ArrowRight className="w-4 h-4 text-slate-400 hidden md:block" />

        <div className="flex flex-col items-center p-3 rounded-xl bg-white border border-violet-200 shadow-sm text-center w-full md:w-auto min-w-[110px]">
          <ShieldCheck className="w-5 h-5 text-violet-600 mb-1" />
          <span className="font-bold text-slate-800">Risk Classifier</span>
          <span className="text-[10px] text-slate-400">Safety Guardrails</span>
        </div>

        <ArrowRight className="w-4 h-4 text-slate-400 hidden md:block" />

        <div className="flex flex-col items-center p-3 rounded-xl bg-white border border-blue-200 shadow-sm text-center w-full md:w-auto min-w-[110px]">
          <Database className="w-5 h-5 text-[#1B5FA8] mb-1" />
          <span className="font-bold text-slate-800">Knowledge Index</span>
          <span className="text-[10px] text-slate-400">Vector Search</span>
        </div>

        <ArrowRight className="w-4 h-4 text-slate-400 hidden md:block" />

        <div className="flex flex-col items-center p-3 rounded-xl bg-green-50 border border-green-300 shadow-sm text-center w-full md:w-auto min-w-[110px]">
          <Cpu className="w-5 h-5 text-[#0E9F6E] mb-1" />
          <span className="font-bold text-[#047857]">Evidence Mode</span>
          <span className="text-[10px] text-green-600">Fallback Path</span>
        </div>
      </div>
    </div>
  );
};
