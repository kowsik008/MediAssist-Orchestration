import React from "react";
import { PageContainer } from "@/components/shell/PageContainer";
import { ReadinessBanner } from "@/components/health/ReadinessBanner";
import { ServiceStatusGrid } from "@/components/health/ServiceStatusGrid";
import { FallbackPath } from "@/components/health/FallbackPath";
import { Activity } from "lucide-react";

export const metadata = {
  title: "System Health & Readiness | MediTrust AI",
  description: "Real-time operational status, degraded mode indicators, and service fallback topology for administrators.",
};

export default function SystemHealthPage() {
  return (
    <PageContainer>
      {/* Page Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-green-50 border border-green-200 text-[#047857] text-xs font-semibold mb-2">
            <Activity className="w-3.5 h-3.5 text-[#0E9F6E]" />
            <span>Operational System Readiness</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
            System Health &amp; Service Readiness
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time operational status, degraded mode indicators, and service fallback topology for administrators.
          </p>
        </div>
      </div>

      <ReadinessBanner overallImpact="Fully operational" />
      <ServiceStatusGrid />
      <FallbackPath />
    </PageContainer>
  );
}

