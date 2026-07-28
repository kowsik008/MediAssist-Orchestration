"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface SurfaceCardProps extends React.HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  variant?: "darkFeature" | "lightFeature" | "featured" | "spotlight" | "transactional" | "default" | "rose" | "amber" | "green";
  children: React.ReactNode;
}

export const SurfaceCard: React.FC<SurfaceCardProps> = ({
  interactive = false,
  variant = "lightFeature",
  className,
  children,
  ...props
}) => {
  const variantStyles = {
    darkFeature:
      "bg-[#1f1633] text-white border border-[#362d59] rounded-2xl p-6",
    lightFeature:
      "bg-white text-[#1f1633] border border-[#e5e7eb] rounded-xl p-6 shadow-sm",
    featured:
      "bg-[#150f23] text-white border border-[#362d59] rounded-xl p-6 shadow-md",
    spotlight:
      "bg-[#422082] text-white border border-[#59349e] rounded-2xl p-6 shadow-md",
    transactional:
      "bg-white text-[#1f1633] border border-[#e5e7eb] rounded-xl p-5 shadow-sm",
    default:
      "bg-white text-[#1f1633] border border-[#e5e7eb] rounded-xl p-5 shadow-sm",
    rose:
      "bg-[#fff1f2] text-[#9f1239] border border-[#fecdd3] rounded-xl p-5",
    amber:
      "bg-[#fffbe0] text-[#92400e] border border-[#fde68a] rounded-xl p-5",
    green:
      "bg-[#f0fdf4] text-[#166534] border border-[#bbf7d0] rounded-xl p-5",
  };

  const interactiveStyle = interactive
    ? "transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md hover:border-[#cfcbd8]"
    : "";

  return (
    <div
      className={cn("relative overflow-hidden", variantStyles[variant], interactiveStyle, className)}
      {...props}
    >
      {children}
    </div>
  );
};
