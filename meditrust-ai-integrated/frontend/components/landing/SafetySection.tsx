"use client";

import React from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { StickerMascot } from "../shared/StickerMascot";
import { ShieldAlert, FileX, Lock, ShieldCheck } from "lucide-react";

export const SafetySection: React.FC = () => {
  const principles = [
    {
      title: "High-Risk Scope Limits",
      description: "Patient-specific dosing, direct prescriptions, and critical emergency treatment selection are automatically withheld and referred to clinical specialists.",
      icon: <ShieldAlert className="w-5 h-5 text-[#fa7faa]" />,
      tag: "Refusal & Referral Guardrails",
      tagBg: "bg-[#fa7faa]/15 border-[#fa7faa]/30 text-white"
    },
    {
      title: "Unsupported Claims Withheld",
      description: "If guidance cannot be fully backed by verified institutional evidence, MediTrust AI explicitly reports insufficient source coverage rather than guessing.",
      icon: <FileX className="w-5 h-5 text-[#c2ef4e]" />,
      tag: "Zero-Hallucination Mandate",
      tagBg: "bg-[#c2ef4e]/15 border-[#c2ef4e]/30 text-[#c2ef4e]"
    },
    {
      title: "Privacy & De-identification",
      description: "Queries must remain aggregated and de-identified. Personal health information (PHI) input is scrubbed prior to knowledge search.",
      icon: <Lock className="w-5 h-5 text-[#23865f]" />,
      tag: "Data Protection Boundary",
      tagBg: "bg-[#23865f]/20 border-[#23865f]/40 text-white"
    }
  ];

  return (
    <section className="py-16 bg-[#1f1633] text-white border-b border-[#362d59] relative">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col md:flex-row items-center justify-between mb-12 gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider text-[#c2ef4e] mb-2">
              <ShieldCheck className="w-4 h-4" />
              <span>Safety By Design</span>
            </div>
            <h2 className="font-display-section text-white">
              Built for Uncompromising Patient Safety
            </h2>
            <p className="text-sm text-[#bbb3c9] mt-2">
              Clear plain-language safety boundaries enforced across every response.
            </p>
          </div>

          {/* Restrained Mascot #2 of 3: Safety Section Mascot */}
          <div className="flex-shrink-0">
            <StickerMascot variant="governed-shield" size="lg" title="Governed Shield Mascot" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {principles.map((item, idx) => (
            <SurfaceCard key={idx} variant="spotlight" className="p-6 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-xl bg-[#150f23] border border-[#59349e] flex items-center justify-center">
                  {item.icon}
                </div>
                <div>
                  <span className={`text-[10px] font-code uppercase tracking-wider px-2 py-0.5 rounded border ${item.tagBg}`}>
                    {item.tag}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-3 mb-2">{item.title}</h3>
                  <p className="text-xs text-[#bbb3c9] leading-relaxed">{item.description}</p>
                </div>
              </div>

              <div className="pt-4 mt-6 border-t border-[#59349e] flex items-center space-x-2 text-[11px] text-[#c2ef4e] font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#c2ef4e]" />
                <span>Enforced Policy Rule</span>
              </div>
            </SurfaceCard>
          ))}
        </div>
      </div>
    </section>
  );
};
