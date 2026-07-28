"use client";

import React from "react";
import { Citation } from "@/lib/types";
import { X, ShieldCheck, FileText } from "lucide-react";
import { ActionButton } from "../shared/ActionButton";

interface EvidenceDrawerProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ citation, isOpen, onClose }) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-[#1f1633]/40 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-lg h-full bg-white border-l border-[#e5e7eb] shadow-2xl p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#f0fdf4] border border-[#bbf7d0] text-[#166534] text-[11px] font-semibold">
                <ShieldCheck className="w-3.5 h-3.5 text-[#23865f]" />
                <span>Verified Source Provenance</span>
              </div>
              <h2 className="text-xl font-bold text-[#1f1633] leading-tight">{citation.title}</h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-[#716a7d] hover:text-[#1f1633] hover:bg-[#f7f6fa] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-xs">
            <div>
              <span className="text-[#716a7d] block mb-0.5">Publisher</span>
              <span className="text-[#1f1633] font-bold">{citation.publisher}</span>
            </div>
            <div>
              <span className="text-[#716a7d] block mb-0.5">Version & Date</span>
              <span className="text-[#1f1633] font-semibold">{citation.versionDate}</span>
            </div>
            <div className="col-span-2 pt-2 border-t border-[#e5e7eb]">
              <span className="text-[#716a7d] block mb-0.5">Target Section</span>
              <span className="text-[#6a5fc1] font-semibold">{citation.section}</span>
            </div>
          </div>

          {/* Excerpt */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#716a7d] uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-[#6a5fc1]" />
              <span>Exact Document Excerpt</span>
            </h3>
            <div className="p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-sm text-[#1f1633] italic leading-relaxed">
              &ldquo;{citation.excerpt}&rdquo;
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[#f0fdf4] border border-[#bbf7d0] text-xs text-[#166534] space-y-1">
            <span className="font-bold text-[#166534]">Citation Integrity Note:</span>
            <p>This excerpt was extracted directly from institutional guidance without modification.</p>
          </div>
        </div>

        <div className="pt-6 border-t border-[#e5e7eb] flex items-center justify-between">
          <span className="text-xs text-[#716a7d]">ID: {citation.sourceId}</span>
          <ActionButton variant="secondary" size="sm" onClick={onClose}>
            Close Drawer
          </ActionButton>
        </div>
      </div>
    </div>
  );
};
