"use client";

import React, { useState, useEffect } from "react";
import { ShieldCheck, Search, FileText, AlertTriangle, ArrowRight, RotateCcw } from "lucide-react";

const sequence = [
  { title: "Clinical Inquiry Entered", duration: 2200 },
  { title: "Approved Guidance Scanned", duration: 2000 },
  { title: "Provenance Verified (3 Sources)", duration: 2200 },
  { title: "Citation Summary Assembled", duration: 2500 },
  { title: "High-Risk Referral Evaluated", duration: 2000 },
];

export const HyperFramesHeroCover: React.FC = () => {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setStepIndex((prev) => (prev + 1) % sequence.length);
    }, sequence[stepIndex].duration);

    return () => clearTimeout(timer);
  }, [stepIndex]);

  return (
    <div className="w-full rounded-2xl bg-[#150f23] border border-[#362d59] p-5 sm:p-6 shadow-2xl space-y-4 font-sans text-left">
      {/* Header bar */}
      <div className="flex items-center justify-between pb-3 border-b border-[#362d59] text-xs">
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#c2ef4e] animate-pulse" />
          <span className="font-code text-white/80 font-bold uppercase tracking-wider text-[11px]">
            Product Story Walkthrough • 8–12s Demo
          </span>
        </div>
        <div className="flex items-center space-x-2 text-[10px] font-code text-white/50">
          <span>Step {stepIndex + 1} of 5</span>
          <button
            onClick={() => setStepIndex(0)}
            className="p-1 rounded hover:bg-white/10 text-white/70 hover:text-white transition-colors"
            title="Restart sequence"
          >
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Story Stage 1: Clinical Query */}
      <div className="space-y-3">
        <div className="p-3.5 rounded-xl bg-[#1f1633] border border-[#362d59] flex items-center space-x-3">
          <Search className="w-4 h-4 text-[#c2ef4e]" />
          <div className="flex-1 text-xs text-white">
            <span className="text-white/40 block text-[10px] font-code">USER QUERY</span>
            <span className="font-medium">&ldquo;What PPE & negative pressure standards apply to aerosolizing viral procedures?&rdquo;</span>
          </div>
        </div>

        {/* Story Stage 2 & 3: Evidence Cards & Verification */}
        {stepIndex >= 1 && (
          <div className="grid grid-cols-3 gap-2 animate-in fade-in slide-in-from-top-2 duration-300">
            <div className={`p-2.5 rounded-lg border text-[11px] transition-all ${stepIndex >= 2 ? "bg-[#23865f]/15 border-[#23865f] text-white" : "bg-[#1f1633] border-[#362d59] text-white/70"}`}>
              <div className="font-bold flex items-center gap-1 text-[10px]">
                <FileText className="w-3 h-3 text-[#c2ef4e]" /> CDC Guideline 4.2
              </div>
              <span className="text-[9px] text-white/60">Airborne Isolation</span>
            </div>

            <div className={`p-2.5 rounded-lg border text-[11px] transition-all ${stepIndex >= 2 ? "bg-[#23865f]/15 border-[#23865f] text-white" : "bg-[#1f1633] border-[#362d59] text-white/70"}`}>
              <div className="font-bold flex items-center gap-1 text-[10px]">
                <ShieldCheck className="w-3 h-3 text-[#23865f]" /> NHS Airborne Standard
              </div>
              <span className="text-[9px] text-white/60">PAPR & N95 Spec</span>
            </div>

            <div className={`p-2.5 rounded-lg border text-[11px] transition-all ${stepIndex >= 2 ? "bg-[#23865f]/15 border-[#23865f] text-white" : "bg-[#1f1633] border-[#362d59] text-white/70"}`}>
              <div className="font-bold flex items-center gap-1 text-[10px]">
                <FileText className="w-3 h-3 text-[#c2ef4e]" /> WHO Infection Doc
              </div>
              <span className="text-[9px] text-white/60">12 ACH Negative Press.</span>
            </div>
          </div>
        )}

        {/* Story Stage 4: Summary Panel */}
        {stepIndex >= 3 && (
          <div className="p-4 rounded-xl bg-white text-[#1f1633] space-y-2 animate-in fade-in duration-300 shadow-md">
            <div className="flex items-center justify-between text-[11px] font-bold border-b border-[#e5e7eb] pb-1.5">
              <span className="text-[#150f23] flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-[#23865f]" /> Governed Citation Summary
              </span>
              <span className="bg-[#23865f]/10 text-[#23865f] px-2 py-0.5 rounded text-[10px]">3 Citations Grounded</span>
            </div>
            <p className="text-xs leading-relaxed text-[#494256]">
              Single-patient negative-pressure room with ≥12 ACH is mandatory. Fit-tested N95 or PAPR required prior to room entry.
            </p>
          </div>
        )}

        {/* Story Stage 5: High-Risk Referral Branch */}
        {stepIndex >= 4 && (
          <div className="p-3 rounded-xl bg-[#fa7faa]/15 border border-[#fa7faa]/40 text-[11px] text-white flex items-center justify-between animate-in fade-in duration-300">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-[#fa7faa]" />
              <div>
                <span className="font-bold block text-white">High-Risk Dosage Query Handled</span>
                <span className="text-[10px] text-white/70">Patient dosing automatically routed to Human Review Beacon.</span>
              </div>
            </div>
            <ArrowRight className="w-4 h-4 text-[#c2ef4e]" />
          </div>
        )}
      </div>

      {/* Timeline indicator */}
      <div className="pt-2 flex items-center space-x-1">
        {sequence.map((s, idx) => (
          <div
            key={idx}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
              idx === stepIndex
                ? "bg-[#c2ef4e]"
                : idx < stepIndex
                ? "bg-[#6a5fc1]"
                : "bg-[#362d59]"
            }`}
          />
        ))}
      </div>
    </div>
  );
};
