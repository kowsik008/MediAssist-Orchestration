"use client";

import React, { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

export const SafetyChart: React.FC = () => {
  const [data, setData] = useState<{ name: string; value: number; color: string }[]>([]);

  useEffect(() => {
    fetch("/api/metrics?window_hours=720", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : null)
      .then((payload) => {
        const stats = payload?.guardrail_stats;
        setData(stats ? [
          { name: "Allowed", value: stats.allowed ?? 0, color: "#0E9F6E" },
          { name: "Blocked", value: stats.blocked ?? 0, color: "#E11D48" },
          { name: "Escalated", value: stats.escalated ?? 0, color: "#D97706" },
        ] : []);
      })
      .catch(() => setData([]));
  }, []);

  const total = data.reduce((sum, item) => sum + item.value, 0);
  return (
    <div className="clinical-panel p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-800">Guardrail Decision Breakdown</h3>
        <span className="text-xs text-rose-600 font-semibold">{total} recorded</span>
      </div>
      {data.length === 0 || total === 0 ? (
        <div className="h-44 grid place-items-center text-xs text-slate-400">No recorded decisions</div>
      ) : (
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={4} dataKey="value">
                {data.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="flex items-center justify-center gap-5 text-[11px] text-slate-500 mt-2">
        {data.map((item) => <span key={item.name}>{item.name}: {item.value}</span>)}
      </div>
    </div>
  );
};
