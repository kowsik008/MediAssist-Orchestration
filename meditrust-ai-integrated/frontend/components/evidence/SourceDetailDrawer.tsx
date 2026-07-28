"use client";

import React from "react";
import { EvidenceSource } from "@/lib/types";
import { StatusBadge } from "../shared/StatusBadge";
import { ActionButton } from "../shared/ActionButton";
import { SyntheticNotice } from "./SyntheticNotice";
import { X, AlertTriangle } from "lucide-react";

interface SourceDetailDrawerProps {
  source: EvidenceSource | null;
  isOpen: boolean;
  onClose: () => void;
}

export const SourceDetailDrawer: React.FC<SourceDetailDrawerProps> = ({ source, isOpen, onClose }) => {
  if (!isOpen || !source) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-[#1f1633]/40 backdrop-blur-sm animate-in fade-in">
      <div className="w-full max-w-xl h-full bg-white border-l border-[#e5e7eb] shadow-2xl p-6 flex flex-col justify-between overflow-y-auto animate-in slide-in-from-right duration-200">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center space-x-2 flex-wrap gap-2">
                <StatusBadge status={source.status} variant={source.status === "Current" ? "success" : "warning"} />
                <span className="text-xs text-[#716a7d] font-code">{source.version}</span>
                {source.isSynthetic && <SyntheticNotice />}
              </div>
              <h2 className="text-xl font-bold text-[#1f1633] leading-tight">{source.title}</h2>
            </div>
            <button onClick={onClose} className="p-2 rounded-xl text-[#716a7d] hover:text-[#1f1633] hover:bg-[#f7f6fa] transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-3 p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-xs">
            <div><span className="text-[#716a7d] block mb-0.5">Publisher</span><span className="text-[#6a5fc1] font-bold">{source.publisher}</span></div>
            <div><span className="text-[#716a7d] block mb-0.5">Publish Date</span><span className="text-[#1f1633] font-semibold">{source.publishDate}</span></div>
            <div><span className="text-[#716a7d] block mb-0.5">Document Type</span><span className="text-[#1f1633] font-semibold">{source.sourceType}</span></div>
            <div><span className="text-[#716a7d] block mb-0.5">Access Role</span><span className="text-[#1f1633] font-semibold">{source.accessRole}</span></div>
          </div>

          {source.isSynthetic && (
            <div className="p-3.5 rounded-xl bg-[#6a5fc1]/10 border border-[#6a5fc1]/30 text-xs text-[#6a5fc1] flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-[#6a5fc1] flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-[#1f1633]">Synthetic Document Notice:</span>
                <p className="text-[#716a7d] mt-0.5">Created exclusively for benchmark evaluation testing. Not styled as approved clinical policy.</p>
              </div>
            </div>
          )}

          {/* Content */}
          <div className="space-y-2">
            <h3 className="text-xs font-bold text-[#716a7d] uppercase tracking-wider">Full Source Content</h3>
            <div className="p-4 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-sm text-[#1f1633] leading-relaxed whitespace-pre-wrap font-sans">
              {source.fullContent}
            </div>
          </div>
        </div>

        <div className="pt-6 border-t border-[#e5e7eb] flex items-center justify-between">
          <span className="text-xs text-[#716a7d]">Document ID: {source.id}</span>
          <ActionButton variant="secondary" size="sm" onClick={onClose}>Close Drawer</ActionButton>
        </div>
      </div>
    </div>
  );
};
