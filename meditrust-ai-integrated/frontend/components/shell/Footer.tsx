"use client";

import React from "react";
import Link from "next/link";
import { Shield, Lock, AlertTriangle } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-[#150f23] text-white border-t border-[#362d59] relative z-20 py-12 mt-auto">
      {/* Restrained Lime Squiggle Divider Location #1 of 1 (Above Footer) */}
      <div className="w-full overflow-hidden mb-8 max-w-7xl mx-auto px-4">
        <svg viewBox="0 0 1200 12" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-3 text-[#c2ef4e]">
          <path d="M0 6 Q 30 0, 60 6 T 120 6 T 180 6 T 240 6 T 300 6 T 360 6 T 420 6 T 480 6 T 540 6 T 600 6 T 660 6 T 720 6 T 780 6 T 840 6 T 900 6 T 960 6 T 1020 6 T 1080 6 T 1140 6 T 1200 6" stroke="currentColor" strokeWidth="2.5" fill="none" />
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-[#1f1633] border border-[#362d59] flex items-center justify-center">
                <Shield className="w-4 h-4 text-[#c2ef4e]" />
              </div>
              <span className="text-base font-bold text-white tracking-wide">MediTrust AI</span>
            </div>
            <p className="text-xs text-[#bbb3c9] leading-relaxed max-w-md">
              Governed healthcare knowledge-support system providing citation-backed clinical and public guidance summaries for healthcare professionals and administrators.
            </p>
            <div className="flex items-start space-x-2 text-[11px] text-white/90 bg-[#1f1633] border border-[#fa7faa]/40 rounded-lg p-2.5 max-w-md">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 text-[#fa7faa] mt-0.5" />
              <span>Responsible-Use Boundary: Knowledge support only. Not for autonomous diagnosis, prescribing, dosage calculation, or emergency care decisions.</span>
            </div>
          </div>

          <div>
            <h4 className="text-xs font-code font-bold text-[#c2ef4e] uppercase tracking-wider mb-3">Public Access</h4>
            <ul className="space-y-2 text-xs text-[#bbb3c9]">
              <li><Link href="/"          className="hover:text-white transition-colors">Overview</Link></li>
              <li><Link href="/assistant" className="hover:text-white transition-colors">Knowledge Assistant</Link></li>
              <li><Link href="/evidence"  className="hover:text-white transition-colors">Evidence Explorer</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-xs font-code font-bold text-[#6a5fc1] uppercase tracking-wider mb-3">Evaluation & Governance</h4>
            <ul className="space-y-2 text-xs text-[#bbb3c9]">
              <li><Link href="/comparison"    className="hover:text-white transition-colors">Evaluator Comparison</Link></li>
              <li><Link href="/governance"    className="hover:text-white transition-colors">Governance & Safety KPIs</Link></li>
              <li><Link href="/system-health" className="hover:text-white transition-colors">System Readiness Health</Link></li>
            </ul>
          </div>
        </div>

        <div className="pt-6 border-t border-[#362d59] flex flex-col sm:flex-row items-center justify-between text-xs text-[#bbb3c9] gap-4">
          <div className="flex items-center space-x-2">
            <Lock className="w-3.5 h-3.5 text-[#23865f]" />
            <span>Audited & Citation-Grounded Healthcare Architecture</span>
          </div>
          <span>© 2026 MediTrust AI. All rights reserved.</span>
        </div>
      </div>
    </footer>
  );
};
