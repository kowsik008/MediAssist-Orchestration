"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className }) => {
  return (
    <div
      className={cn("animate-pulse rounded-lg bg-slate-200 border border-slate-100", className)}
    />
  );
};
