"use client";

import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export const RetrievalChart: React.FC = () => {
  const [data, setData] = useState<{ name: string; value: number }[]>([]);

  useEffect(() => {
    fetch("/api/metrics?window_hours=720", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        const stats = payload?.retrieval_stats;
        setData(stats ? [
          { name: "Retrievals", value: stats.total_retrievals ?? 0 },
          { name: "Cache hits", value: stats.cache_hits ?? 0 },
          { name: "Cache misses", value: stats.cache_misses ?? 0 },
        ] : []);
      })
      .catch(() => setData([]));
  }, []);

  return (
    <div className="clinical-panel p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-800">Recorded Retrieval Activity</h3>
        <span className="text-xs text-[#1B5FA8] font-semibold">Last 30 Days</span>
      </div>
      {data.length === 0 ? (
        <div className="h-44 grid place-items-center text-xs text-slate-400">Metrics unavailable</div>
      ) : (
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <XAxis dataKey="name" stroke="#94A3B8" fontSize={11} />
              <YAxis allowDecimals={false} stroke="#94A3B8" fontSize={11} />
              <Tooltip />
              <Bar dataKey="value" fill="#1B5FA8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};
