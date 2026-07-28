"use client";

import React from "react";
import { CautionItem } from "@/lib/types";
import { AlertTriangle } from "lucide-react";

interface CautionPanelProps {
  cautions: CautionItem[];
}

export const CautionPanel: React.FC<CautionPanelProps> = ({ cautions }) => {
  if (!cautions || cautions.length === 0) return null;

  return (
    <div className="my-3 space-y-2">
      {cautions.map((item) => (
        <div
          key={item.id}
          className="p-3 rounded-xl bg-[#fffbe0] border border-[#fde68a] text-xs text-[#92400e] flex items-start space-x-2.5"
        >
          <AlertTriangle className="w-4 h-4 text-[#a66a00] flex-shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold text-[#78350f]">Caution ({item.statementReference}):</span>
            <p className="text-[#92400e] leading-relaxed">{item.text}</p>
          </div>
        </div>
      ))}
    </div>
  );
};
