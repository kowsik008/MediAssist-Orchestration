"use client";

import React from "react";
import { AlertCircle } from "lucide-react";

export const SyntheticNotice: React.FC = () => {
  return (
    <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-violet-50 border border-violet-200 text-violet-700 text-[10px] font-semibold">
      <AlertCircle className="w-3 h-3 text-violet-500" />
      <span>Synthetic Demonstration Record</span>
    </div>
  );
};
