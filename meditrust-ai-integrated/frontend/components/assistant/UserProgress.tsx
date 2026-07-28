"use client";

import React from "react";
import { PlainProgressStep } from "@/lib/types";
import { Loader2, CheckCircle2, ShieldCheck } from "lucide-react";

interface UserProgressProps {
  currentStepIndex: number;
  steps: PlainProgressStep[];
}

export const UserProgress: React.FC<UserProgressProps> = ({ currentStepIndex, steps }) => {
  return (
    <div className="p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] my-4 space-y-3 animate-in fade-in shadow-sm">
      <div className="flex items-center space-x-2 text-xs font-bold text-[#1f1633]">
        <ShieldCheck className="w-4 h-4 text-[#23865f] animate-pulse" />
        <span>Reviewing Guidance Sources</span>
      </div>

      <div className="space-y-2">
        {steps.map((step, idx) => {
          const isDone    = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;

          return (
            <div key={idx} className="flex items-center space-x-3 text-xs">
              {isDone ? (
                <CheckCircle2 className="w-4 h-4 text-[#23865f] flex-shrink-0" />
              ) : isCurrent ? (
                <Loader2 className="w-4 h-4 text-[#6a5fc1] animate-spin flex-shrink-0" />
              ) : (
                <div className="w-4 h-4 rounded-full border-2 border-[#e5e7eb] flex-shrink-0" />
              )}
              <span className={isDone ? "text-[#716a7d] line-through" : isCurrent ? "text-[#1f1633] font-bold" : "text-[#716a7d]"}>
                {step}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
