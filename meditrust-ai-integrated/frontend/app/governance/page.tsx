import React from "react";
import { PageContainer } from "@/components/shell/PageContainer";
import { KPICard } from "@/components/governance/KPICard";
import { RetrievalChart } from "@/components/governance/RetrievalChart";
import { SafetyChart } from "@/components/governance/SafetyChart";
import { AuditTable } from "@/components/governance/AuditTable";
import { ShieldCheck } from "lucide-react";

export const metadata = {
  title: "Governance & Safety KPIs | MediTrust AI",
  description: "System performance benchmarks, retrieval precision, and audit event logs for compliance administrators.",
};

export default function GovernancePage() {
  return (
    <PageContainer>
      {/* Page Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
        <div>
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-violet-50 border border-violet-200 text-violet-700 text-xs font-semibold mb-2">
            <ShieldCheck className="w-3.5 h-3.5 text-violet-500" />
            <span>Operational &amp; Governance Insight Area</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
            Governance &amp; Safety KPIs
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            System performance benchmarks, retrieval precision, and audit event logs for compliance administrators.
          </p>
        </div>
      </div>

      <KPICard />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 my-6">
        <RetrievalChart />
        <SafetyChart />
      </div>

      <AuditTable />
    </PageContainer>
  );
}
