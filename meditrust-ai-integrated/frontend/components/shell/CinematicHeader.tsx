"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PublicNavigation } from "./PublicNavigation";
import { MobileNavigation } from "./MobileNavigation";
import { Shield, Sparkles } from "lucide-react";
import { ActionButton } from "../shared/ActionButton";

export const CinematicHeader: React.FC = () => {
  const pathname = usePathname();
  const isMarketing = pathname === "/";

  return (
    <header
      className={`sticky top-0 z-40 w-full transition-colors duration-200 ${
        isMarketing
          ? "bg-[#150f23]/95 backdrop-blur-md border-b border-[#362d59] text-white"
          : "bg-white/95 backdrop-blur-md border-b border-[#e5e7eb] text-[#1f1633] shadow-sm"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-lg bg-[#1f1633] border border-[#362d59] flex items-center justify-center group-hover:border-[#c2ef4e] transition-colors shadow-sm">
            <Shield className="w-5 h-5 text-[#c2ef4e]" />
          </div>
          <div className="flex flex-col">
            <span className={`text-base font-bold tracking-tight flex items-center gap-2 ${isMarketing ? "text-white" : "text-[#1f1633]"}`}>
              MediTrust AI
              <span className="text-[10px] px-1.5 py-0.2 font-code font-bold bg-[#c2ef4e] text-[#1f1633] rounded tracking-wide">
                GOVERNED
              </span>
            </span>
            <span className={`text-[10px] -mt-0.5 tracking-wider font-semibold ${isMarketing ? "text-[#bbb3c9]" : "text-[#716a7d]"}`}>
              HEALTHCARE KNOWLEDGE
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <PublicNavigation isMarketing={isMarketing} />

        {/* CTA + Mobile Trigger */}
        <div className="flex items-center space-x-3">
          <Link href="/assistant" className="hidden sm:inline-flex">
            <ActionButton variant={isMarketing ? "inverted" : "primary"} size="sm">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ask Assistant</span>
            </ActionButton>
          </Link>
          <MobileNavigation />
        </div>
      </div>
    </header>
  );
};
