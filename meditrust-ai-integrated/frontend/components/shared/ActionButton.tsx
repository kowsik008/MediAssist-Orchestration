"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface ActionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "inverted" | "ghost-dark" | "violet" | "danger" | "secondary";
  size?: "sm" | "md" | "lg";
  children: React.ReactNode;
}

export const ActionButton: React.FC<ActionButtonProps> = ({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center button-cap rounded-lg transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.99]";

  const variants = {
    // Primary: Filled dark midnight-violet with white type
    primary:
      "bg-[#150f23] text-white hover:bg-[#251c3d] focus:ring-[#6a5fc1] shadow-sm",
    // Inverted: Filled white with dark midnight type (for dark hero canvas)
    inverted:
      "bg-white text-[#1f1633] hover:bg-[#f0edf5] focus:ring-white shadow-md font-bold",
    // Ghost-Dark: Translucent fill on dark canvas
    "ghost-dark":
      "bg-white/10 hover:bg-white/18 text-white border border-white/15 focus:ring-white/30",
    // Violet: Category / token button
    violet:
      "bg-[#79628c] text-white hover:bg-[#68527b] border border-[#68527b] focus:ring-[#79628c]",
    // Danger: Safety refusal / alert button
    danger:
      "bg-[#fff1f2] border border-[#fecdd3] text-[#b5414c] hover:bg-[#ffe4e6] focus:ring-[#b5414c]",
    // Secondary: Light surface clean border button
    secondary:
      "bg-white text-[#1f1633] border border-[#e5e7eb] hover:bg-[#f7f6fa] hover:border-[#cfcbd8] focus:ring-[#6a5fc1] shadow-sm font-semibold",
  };

  const sizes = {
    sm: "px-3.5 py-2 text-xs gap-1.5",
    md: "px-4.5 py-2.5 text-xs gap-2",
    lg: "px-6 py-3 text-sm gap-2.5",
  };

  return (
    <button
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      {...props}
    >
      {children}
    </button>
  );
};
