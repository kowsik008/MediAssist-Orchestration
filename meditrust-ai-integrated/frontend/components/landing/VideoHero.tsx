"use client";

import React from "react";
import Link from "next/link";
import { ActionButton } from "../shared/ActionButton";
import { StickerMascot } from "../shared/StickerMascot";
import { HyperFramesHeroCover } from "./HyperFramesHeroCover";
import { ShieldCheck, ArrowRight, BookOpen, Sparkles } from "lucide-react";

export const VideoHero: React.FC = () => {
  return (
    <section className="relative w-full overflow-hidden starfield-bg text-white border-b border-[#362d59]">
      {/* Restrained Mascot #1 of 3: Top-Right Hero Junction */}
      <div className="absolute top-8 right-8 hidden lg:block z-20">
        <StickerMascot variant="evidence-navigator" size="lg" title="Evidence Navigator" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center flex flex-col items-center">
        {/* Eyebrow Badge */}
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-white/10 border border-white/15 text-[#c2ef4e] text-xs font-semibold mb-6 shadow-sm">
          <ShieldCheck className="w-3.5 h-3.5 text-[#c2ef4e]" />
          <span>Governed Healthcare Knowledge Support</span>
        </div>

        {/* Hero Headline — Space Grotesk + Max ONE Lime Keyword Chip */}
        <h1 className="font-display-hero text-white max-w-4xl mb-6">
          Trusted guidance for{" "}
          <span className="chip-lime-keyword">critical decisions</span>.
        </h1>

        {/* Sub-headline */}
        <p className="text-base sm:text-lg text-[#bbb3c9] max-w-2xl font-normal leading-relaxed mb-8">
          Search approved clinical protocols, review supporting evidence, and receive concise citation-backed summaries tailored for healthcare teams.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-3 mb-10 w-full sm:w-auto">
          <Link href="/assistant" className="w-full sm:w-auto">
            <ActionButton variant="inverted" size="lg" className="w-full sm:w-auto group">
              <Sparkles className="w-4 h-4 text-[#1f1633]" />
              <span>Open Assistant</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </ActionButton>
          </Link>
          <Link href="/evidence" className="w-full sm:w-auto">
            <ActionButton variant="ghost-dark" size="lg" className="w-full sm:w-auto">
              <BookOpen className="w-4 h-4 text-[#c2ef4e]" />
              <span>Explore Evidence</span>
            </ActionButton>
          </Link>
        </div>

        {/* HyperFrames Hero Cover Animation Card */}
        <div className="w-full max-w-3xl mb-8">
          <HyperFramesHeroCover />
        </div>

        {/* Responsible-Use Notice */}
        <div className="inline-flex items-center space-x-2 text-xs text-[#bbb3c9] bg-[#150f23]/90 border border-[#362d59] rounded-xl px-4 py-2 shadow-sm">
          <span className="w-2 h-2 rounded-full bg-[#23865f] animate-pulse flex-shrink-0" />
          <span>Knowledge support only — no autonomous diagnosis, prescribing, or dosage calculation.</span>
        </div>
      </div>
    </section>
  );
};
