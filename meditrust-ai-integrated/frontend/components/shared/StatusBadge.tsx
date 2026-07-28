"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  variant?: "success" | "warning" | "danger" | "info" | "neutral" | "synthetic";
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = "info",
  className,
}) => {
  const styles = {
    success:   "bg-green-50 border-green-200 text-green-700",
    warning:   "bg-amber-50 border-amber-200 text-amber-700",
    danger:    "bg-rose-50  border-rose-200  text-rose-700",
    info:      "bg-blue-50  border-blue-200  text-blue-700",
    neutral:   "bg-slate-100 border-slate-200 text-slate-600",
    synthetic: "bg-violet-50 border-violet-200 text-violet-700",
  };

  const dotColor = {
    success:   "bg-green-500",
    warning:   "bg-amber-500",
    danger:    "bg-rose-500",
    info:      "bg-blue-500",
    neutral:   "bg-slate-400",
    synthetic: "bg-violet-500",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border",
        styles[variant],
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full mr-1.5 animate-pulse", dotColor[variant])} />
      {status}
    </span>
  );
};
