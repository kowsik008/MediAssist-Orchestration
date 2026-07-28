"use client";

import React from "react";
import { ComparisonScenario } from "@/lib/types";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface ResponseTimeChartProps {
  scenario: ComparisonScenario;
}

export const ResponseTimeChart: React.FC<ResponseTimeChartProps> = ({ scenario }) => {
  const data = [
    { name: "Standard LLM", timeMs: scenario.responseTimeBefore, color: "#94A3B8" },
    { name: "MediTrust Governed", timeMs: scenario.responseTimeAfter, color: "#1B5FA8" },
  ];

  return (
    <div className="clinical-panel p-5 my-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-800">Response Time Comparison (Milliseconds)</h3>
        <span className="text-xs text-[#0E9F6E] font-semibold">Lower is faster</span>
      </div>

      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <XAxis type="number" stroke="#94A3B8" fontSize={12} unit=" ms" />
            <YAxis type="category" dataKey="name" stroke="#94A3B8" fontSize={12} width={130} />
            <Tooltip contentStyle={{ backgroundColor: "#fff", borderColor: "#E2E8F0", borderRadius: "8px", color: "#0F172A" }} formatter={(value) => [`${value} ms`, "Response Latency"]} />
            <Bar dataKey="timeMs" radius={[0, 8, 8, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-600 bg-blue-50 border border-blue-100 p-3 rounded-xl">
        <span className="font-bold text-[#1B5FA8]">Interpretation:</span> MediTrust AI delivers citation-backed answers in <span className="font-bold text-slate-900">{scenario.responseTimeAfter} ms</span> compared to <span className="font-bold text-slate-500">{scenario.responseTimeBefore} ms</span> for un-governed LLM queries, providing a faster and safer experience for clinical staff.
      </div>
    </div>
  );
};
