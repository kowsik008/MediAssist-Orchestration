"use client";

import React from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { ImageWithFallback } from "../shared/ImageWithFallback";
import { CheckCircle2, UserCheck, Shield, Clock } from "lucide-react";

export const TrustStory: React.FC = () => {
  return (
    <section className="py-16 bg-[#ffffff] text-[#1f1633] border-b border-[#e5e7eb]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Text Column */}
          <div className="lg:col-span-6 space-y-6">
            <div className="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-[#6a5fc1]">
              <Shield className="w-4 h-4 text-[#23865f]" />
              <span>Designed For Healthcare Teams</span>
            </div>
            <h2 className="font-display-section text-[#1f1633]">
              Human-centered guidance, grounded in verified protocols.
            </h2>
            <p className="text-sm sm:text-base text-[#494256] leading-relaxed font-normal">
              MediTrust AI delivers instant access to official institutional guidelines and clinical protocols. By translating complex source materials into concise, citation-backed answers, clinicians make informed decisions faster without sacrificing safety.
            </p>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] space-y-1">
                <div className="flex items-center space-x-2 text-[#1f1633] font-bold text-sm">
                  <CheckCircle2 className="w-4 h-4 text-[#23865f]" />
                  <span>100% Traceable</span>
                </div>
                <p className="text-xs text-[#716a7d]">Every response links directly to exact sections in approved source documents.</p>
              </div>

              <div className="p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] space-y-1">
                <div className="flex items-center space-x-2 text-[#23865f] font-bold text-sm">
                  <Clock className="w-4 h-4" />
                  <span>Time-Efficient</span>
                </div>
                <p className="text-xs text-[#716a7d]">Reduces routine guidance retrieval from minutes to seconds for staff.</p>
              </div>
            </div>
          </div>

          {/* Browser Frame Demonstration Column */}
          <div className="lg:col-span-6">
            <SurfaceCard variant="lightFeature" className="p-2 border-[#cfcbd8] relative overflow-hidden group shadow-lg">
              {/* Browser Header Bar */}
              <div className="flex items-center space-x-1.5 px-3 py-2 bg-[#f7f6fa] border-b border-[#e5e7eb] rounded-t-lg">
                <span className="w-3 h-3 rounded-full bg-[#fa7faa]" />
                <span className="w-3 h-3 rounded-full bg-[#fde68a]" />
                <span className="w-3 h-3 rounded-full bg-[#23865f]" />
                <span className="text-[11px] font-code text-[#716a7d] ml-2">meditrust-assistant.local/demo</span>
              </div>

              <div className="relative aspect-[16/10] rounded-b-lg overflow-hidden min-h-[260px] bg-[#f7f6fa]">
                <ImageWithFallback
                  src="/images/trust_story_team.png"
                  alt="Healthcare team reviewing clinical guidance together"
                  fill
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#1f1633]/60 via-transparent to-transparent pointer-events-none" />
                <div className="absolute bottom-4 left-4 right-4 p-3 rounded-xl bg-white/90 backdrop-blur-md border border-white shadow-md text-xs text-[#1f1633] flex items-center justify-between z-10">
                  <div className="flex items-center space-x-2">
                    <UserCheck className="w-4 h-4 text-[#6a5fc1] flex-shrink-0" />
                    <span className="font-bold">Active Verification Status: Grounded</span>
                  </div>
                  <span className="text-[10px] font-code text-[#716a7d]">v4.2</span>
                </div>
              </div>
            </SurfaceCard>
          </div>
        </div>
      </div>
    </section>
  );
};
