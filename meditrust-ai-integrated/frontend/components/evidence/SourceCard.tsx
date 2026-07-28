"use client";

import React from "react";
import { EvidenceSource } from "@/lib/types";
import { SurfaceCard } from "../shared/SurfaceCard";
import { StatusBadge } from "../shared/StatusBadge";
import { SyntheticNotice } from "./SyntheticNotice";
import { SourceThumbnail } from "./SourceThumbnail";
import { BookOpen, User, ExternalLink } from "lucide-react";

interface SourceCardProps {
  source: EvidenceSource;
  onSelect: (source: EvidenceSource) => void;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source, onSelect }) => {
  const getBadgeVariant = (status: string) => {
    switch (status) {
      case "Current":              return "success";
      case "Superseded":           return "warning";
      case "Expired":              return "danger";
      case "Demonstration only":   return "synthetic";
      default:                     return "info";
    }
  };

  return (
    <SurfaceCard
      variant="transactional"
      interactive
      onClick={() => onSelect(source)}
      className="flex flex-col justify-between h-full p-4 border-[#e5e7eb] cursor-pointer group"
    >
      <div className="space-y-3">
        <SourceThumbnail src={source.thumbnailUrl} alt={source.title} />

        <div className="flex items-center justify-between gap-2 flex-wrap">
          <StatusBadge status={source.status} variant={getBadgeVariant(source.status)} />
          {source.isSynthetic && <SyntheticNotice />}
        </div>

        <h3 className="text-base font-bold text-[#1f1633] group-hover:text-[#6a5fc1] transition-colors line-clamp-2 leading-snug">
          {source.title}
        </h3>

        <div className="space-y-1 text-xs text-[#716a7d]">
          <div className="flex items-center space-x-1.5 text-[#6a5fc1] font-semibold">
            <BookOpen className="w-3.5 h-3.5" />
            <span>{source.publisher}</span>
          </div>
          <span className="text-[#716a7d] text-[11px] font-code">{source.publishDate} • {source.version}</span>
        </div>

        <div className="p-3 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-xs text-[#494256] italic line-clamp-3">
          &ldquo;{source.excerpt}&rdquo;
        </div>
      </div>

      <div className="pt-4 mt-4 border-t border-[#e5e7eb] flex items-center justify-between text-xs text-[#716a7d]">
        <span className="flex items-center gap-1 text-[11px]">
          <User className="w-3 h-3 text-[#6a5fc1]" />
          {source.accessRole}
        </span>
        <span className="text-[#6a5fc1] group-hover:underline flex items-center gap-1 font-bold">
          Inspect drawer <ExternalLink className="w-3 h-3" />
        </span>
      </div>
    </SurfaceCard>
  );
};
