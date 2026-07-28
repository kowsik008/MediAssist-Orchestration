import React from "react";
import { PageContainer } from "@/components/shell/PageContainer";
import { ComparisonRunner } from "@/components/comparison/ComparisonRunner";
import { GitCompare } from "lucide-react";

export const metadata = {
  title: "Evaluator Comparison | MediTrust AI",
  description: "Compare governed MediTrust AI outputs directly against un-governed standard LLM baselines.",
};

export default function ComparisonPage() {
  return (
    <PageContainer>
      {/* Page Header */}
      <div className="pb-4 border-b border-slate-200 mb-6">
        <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-[#1B5FA8] text-xs font-semibold mb-2">
          <GitCompare className="w-3.5 h-3.5" />
          <span>Evaluator Benchmark Suite</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
          Evaluator Outcome Comparison
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Compare governed MediTrust AI outputs directly against un-governed standard LLM baselines.
        </p>
      </div>

      <ComparisonRunner />
    </PageContainer>
  );
}
