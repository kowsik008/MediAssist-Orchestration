"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";

interface ReadinessBannerProps {
  overallImpact?: string;
}

export const ReadinessBanner: React.FC<ReadinessBannerProps> = ({ overallImpact = "Fully operational" }) => {
  const isDegraded = overallImpact !== "Fully operational";

  return (
    <div className={`clinical-panel p-6 my-4 ${isDegraded ? "clinical-panel-amber" : "clinical-panel-green"}`}>
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-xl ${isDegraded ? "bg-amber-100 text-amber-600" : "bg-green-100 text-[#0E9F6E]"}`}>
            {isDegraded ? <AlertTriangle className="w-6 h-6" /> : <CheckCircle2 className="w-6 h-6" />}
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">System Impact Status</span>
            <h2 className="text-xl font-extrabold text-slate-900">{overallImpact}</h2>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-600 bg-white border border-slate-200 p-3 rounded-xl shadow-sm">
          <ShieldCheck className="w-4 h-4 text-[#0E9F6E]" />
          <span>Core Guidance Retrieval & Evidence Base Active</span>
        </div>
      </div>
    </div>
  );
};
