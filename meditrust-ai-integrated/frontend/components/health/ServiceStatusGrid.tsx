"use client";

import React, { useEffect, useState } from "react";
import { fetchServices } from "@/lib/api-client";
import { ServiceStatus } from "@/lib/types";
import { StatusBadge } from "../shared/StatusBadge";

interface ServiceStatusGridProps {
  services?: ServiceStatus[];
}

export const ServiceStatusGrid: React.FC<ServiceStatusGridProps> = ({ services: initialServices }) => {
  const [services, setServices] = useState<ServiceStatus[]>(initialServices || []);
  const [loading, setLoading] = useState(!initialServices);

  useEffect(() => {
    if (!initialServices) {
      fetchServices().then((data) => {
        setServices(data);
        setLoading(false);
      });
    }
  }, [initialServices]);

  if (loading) {
    return <div className="text-center py-12 text-xs text-slate-400">Loading service metrics...</div>;
  }

  if (services.length === 0) {
    return <div className="text-center py-12 text-xs text-slate-400">No service metrics currently available.</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
      {services.map((svc) => (
        <div key={svc.id} className="clinical-panel p-4 flex flex-col justify-between space-y-3">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-slate-400 uppercase">{svc.name}</span>
              <StatusBadge status={svc.status} variant={svc.status === "Operational" ? "success" : "warning"} />
            </div>
            <h3 className="text-sm font-bold text-slate-800">{svc.displayName}</h3>
          </div>

          <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">User Impact:</span>
              <span className="text-[#1B5FA8] font-semibold">{svc.plainLanguageImpact}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Latency:</span>
              <span className="text-slate-700 font-mono">{svc.latencyMs} ms</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Measurement:</span>
              <span className="text-[#0E9F6E] font-mono font-bold">Live check</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
