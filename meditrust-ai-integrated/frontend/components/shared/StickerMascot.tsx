"use client";

import React from "react";
import { cn } from "@/lib/utils";

export type StickerMascotVariant =
  | "evidence-navigator"
  | "governed-shield"
  | "knowledge-guide"
  | "human-review";

interface StickerMascotProps {
  variant: StickerMascotVariant;
  size?: "sm" | "md" | "lg" | "xl";
  decorative?: boolean;
  title?: string;
  className?: string;
}

export const StickerMascot: React.FC<StickerMascotProps> = ({
  variant,
  size = "md",
  decorative = true,
  title,
  className,
}) => {
  const sizeMap = {
    sm: "w-10 h-10",
    md: "w-16 h-16",
    lg: "w-24 h-24",
    xl: "w-32 h-32",
  };

  const renderGraphic = () => {
    switch (variant) {
      case "evidence-navigator":
        return (
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            <circle cx="32" cy="32" r="28" stroke="#1f1633" strokeWidth="3" fill="#ffffff" />
            <circle cx="32" cy="32" r="22" stroke="#6a5fc1" strokeWidth="2" strokeDasharray="4 4" fill="none" />
            <polygon points="32,16 38,32 32,28 26,32" fill="#c2ef4e" stroke="#1f1633" strokeWidth="2" />
            <polygon points="32,48 38,32 32,36 26,32" fill="#6a5fc1" stroke="#1f1633" strokeWidth="2" />
            <circle cx="32" cy="32" r="3" fill="#1f1633" />
          </svg>
        );

      case "governed-shield":
        return (
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            <path d="M32 6L10 14V30C10 44 20 54 32 58C44 54 54 44 54 30V14L32 6Z" fill="#1f1633" stroke="#1f1633" strokeWidth="3" />
            <path d="M32 10L14 17V30C14 42 22 50 32 54C42 50 50 42 50 30V17L32 10Z" fill="#150f23" />
            <path d="M24 32L30 38L42 24" stroke="#c2ef4e" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        );

      case "knowledge-guide":
        return (
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            <rect x="8" y="12" width="48" height="40" rx="6" fill="#ffffff" stroke="#1f1633" strokeWidth="3" />
            <line x1="32" y1="12" x2="32" y2="52" stroke="#1f1633" strokeWidth="2" />
            <line x1="16" y1="22" x2="26" y2="22" stroke="#6a5fc1" strokeWidth="3" strokeLinecap="round" />
            <line x1="16" y1="30" x2="28" y2="30" stroke="#1f1633" strokeWidth="2" strokeLinecap="round" />
            <line x1="16" y1="38" x2="24" y2="38" stroke="#1f1633" strokeWidth="2" strokeLinecap="round" />
            <line x1="38" y1="22" x2="48" y2="22" stroke="#c2ef4e" strokeWidth="3" strokeLinecap="round" />
            <line x1="38" y1="30" x2="48" y2="30" stroke="#1f1633" strokeWidth="2" strokeLinecap="round" />
            <circle cx="44" cy="40" r="4" fill="#fa7faa" />
          </svg>
        );

      case "human-review":
        return (
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
            <circle cx="32" cy="32" r="26" fill="#fff1f2" stroke="#b5414c" strokeWidth="3" />
            <path d="M32 16V36" stroke="#b5414c" strokeWidth="4" strokeLinecap="round" />
            <circle cx="32" cy="44" r="3" fill="#b5414c" />
          </svg>
        );
    }
  };

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center p-2 rounded-2xl bg-white/90 border border-[#1f1633]/15 shadow-sm transition-transform duration-200 hover:scale-105",
        sizeMap[size],
        className
      )}
      aria-hidden={decorative ? "true" : undefined}
      role={decorative ? undefined : "img"}
      aria-label={decorative ? undefined : title || variant}
    >
      {renderGraphic()}
    </div>
  );
};
