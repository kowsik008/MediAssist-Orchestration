"use client";

import React, { useEffect, useState } from "react";
import { fetchAuditLogs } from "@/lib/api-client";
import { AuditEvent } from "@/lib/types";
import { StatusBadge } from "../shared/StatusBadge";
import { ShieldCheck, Eye } from "lucide-react";

interface AuditTableProps {
  onSelectEvent?: (eventId: string) => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({ onSelectEvent }) => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAuditLogs().then((data) => {
      setLogs(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="clinical-panel p-5 my-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#0E9F6E]" />
            Guardrail Event & Safety Audit Log
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Aggregated request identifiers and risk decision classifications (raw sensitive text scrubbed).
          </p>
        </div>
        <span className="text-[11px] text-[#0E9F6E] font-bold bg-green-50 border border-green-200 px-2.5 py-0.5 rounded-full">PHI Scrubbing Active</span>
      </div>

      {loading ? (
        <div className="text-center py-8 text-xs text-slate-400">Loading audit logs...</div>
      ) : logs.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-400">No safety audit logs recorded.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-400 font-bold text-[10px] uppercase tracking-wider">
              <tr>
                <th className="p-3">Request ID</th>
                <th className="p-3">Timestamp</th>
                <th className="p-3">Risk Category</th>
                <th className="p-3">Governance Decision</th>
                <th className="p-3">Human-Review Status</th>
                <th className="p-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((evt) => (
                <tr key={evt.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3 font-mono text-[#1B5FA8] font-bold">{evt.requestId}</td>
                  <td className="p-3 text-slate-400">{evt.timestamp}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                      evt.riskCategory === "High"   ? "bg-rose-50   text-rose-700   border-rose-200" :
                      evt.riskCategory === "Medium" ? "bg-amber-50  text-amber-700  border-amber-200" :
                                                      "bg-green-50  text-green-700  border-green-200"
                    }`}>{evt.riskCategory}</span>
                  </td>
                  <td className="p-3 font-semibold text-slate-700">{evt.decision}</td>
                  <td className="p-3">
                    <StatusBadge status={evt.humanReviewStatus} variant={evt.humanReviewStatus === "Escalated" ? "warning" : "success"} />
                  </td>
                  <td className="p-3 text-right">
                    <button onClick={() => onSelectEvent?.(evt.id)} className="p-1 rounded text-slate-400 hover:text-[#1B5FA8] transition-colors">
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

