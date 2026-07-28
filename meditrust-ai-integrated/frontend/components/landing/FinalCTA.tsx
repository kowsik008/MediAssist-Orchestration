"use client";

import React from "react";
import Link from "next/link";
import { ActionButton } from "../shared/ActionButton";
import { Sparkles, BookOpen, ShieldCheck } from "lucide-react";

export const FinalCTA: React.FC = () => {
  return (
    <section className="py-20 starfield-bg text-white border-t border-[#362d59]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-white/15 text-[#c2ef4e] text-xs font-semibold shadow-sm">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Governed & Audited Healthcare Assistant</span>
        </div>

        <h2 className="font-display-section text-white max-w-2xl mx-auto">
          Ready to explore verified healthcare guidance?
        </h2>

        <p className="text-sm sm:text-base text-[#bbb3c9] font-normal max-w-xl mx-auto">
          Experience citation-backed knowledge support designed with strict patient safety guardrails and plain-language evidence tracing.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link href="/assistant" className="w-full sm:w-auto">
            <ActionButton variant="inverted" size="lg" className="w-full sm:w-auto">
              <Sparkles className="w-4 h-4 text-[#1f1633]" />
              <span>Launch Assistant</span>
            </ActionButton>
          </Link>
          <Link href="/evidence" className="w-full sm:w-auto">
            <ActionButton variant="ghost-dark" size="lg" className="w-full sm:w-auto">
              <BookOpen className="w-4 h-4 text-[#c2ef4e]" />
              <span>Browse Source Evidence</span>
            </ActionButton>
          </Link>
        </div>
      </div>
    </section>
  );
};
