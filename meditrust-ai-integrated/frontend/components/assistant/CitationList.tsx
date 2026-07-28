"use client";

import React from "react";
import { Citation } from "@/lib/types";
import { BookOpen, ExternalLink } from "lucide-react";

interface CitationListProps {
  citations: Citation[];
  onOpenDrawer: (citation: Citation) => void;
}

export const CitationList: React.FC<CitationListProps> = ({ citations, onOpenDrawer }) => {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-[#e5e7eb] space-y-2">
      <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-[#23865f]">
        <BookOpen className="w-3.5 h-3.5" />
        <span>Cited Evidence Sources ({citations.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {citations.map((cite) => (
          <button
            key={cite.id}
            onClick={() => onOpenDrawer(cite)}
            className="flex items-center justify-between p-2.5 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] hover:border-[#6a5fc1] text-left transition-colors group shadow-sm cursor-pointer"
          >
            <div className="space-y-0.5 max-w-[85%]">
              <div className="text-xs font-bold text-[#1f1633] truncate">{cite.title}</div>
              <div className="text-[11px] text-[#6a5fc1] font-semibold">
                {cite.publisher} • <span className="text-[#716a7d] font-normal">{cite.versionDate}</span>
              </div>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-[#716a7d] group-hover:text-[#6a5fc1] transition-colors flex-shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
};
