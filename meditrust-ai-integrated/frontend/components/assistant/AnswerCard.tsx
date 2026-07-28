"use client";

import React from "react";
import { AssistantMessage, Citation } from "@/lib/types";
import { SurfaceCard } from "../shared/SurfaceCard";
import { CautionPanel } from "./CautionPanel";
import { CitationList } from "./CitationList";
import { AlertCircle, ShieldCheck, ShieldAlert, Sparkles, User } from "lucide-react";

interface AnswerCardProps {
  message: AssistantMessage;
  onOpenCitationDrawer: (citation: Citation) => void;
}

export const AnswerCard: React.FC<AnswerCardProps> = ({ message, onOpenCitationDrawer }) => {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end my-4 animate-in fade-in">
        <div className="max-w-2xl bg-[#1f1633] rounded-2xl px-5 py-4 text-white space-y-1 shadow-sm">
          <div className="flex items-center justify-between text-[11px] text-[#bbb3c9] font-medium mb-1">
            <span className="flex items-center gap-1.5 font-code">
              <User className="w-3.5 h-3.5 text-[#c2ef4e]" />
              <span>{message.userRole || "Healthcare Staff"} Inquiry</span>
            </span>
            <span className="text-[#bbb3c9] font-code">{message.timestamp}</span>
          </div>
          <p className="text-sm font-normal leading-relaxed">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.isUnavailable) {
    return (
      <SurfaceCard variant="transactional" className="my-4 p-5 space-y-3 border-amber-200 bg-amber-50">
        <div className="flex items-center space-x-2 text-amber-800 font-bold text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>Assistant Service Unavailable</span>
        </div>
        <p className="text-xs text-amber-900 leading-relaxed font-semibold">
          {message.withheldReason || "A required service could not be reached."}
        </p>
        <div className="pt-3 border-t border-amber-200 text-[11px] text-amber-800">
          No clinical decision was made and no human-review escalation was triggered. Please retry.
        </div>
      </SurfaceCard>
    );
  }

  // Withheld / High-Risk state
  if (message.isWithheld) {
    return (
      <SurfaceCard variant="rose" className="my-4 p-5 space-y-3">
        <div className="flex items-center space-x-2 text-[#b5414c] font-bold text-sm">
          <ShieldAlert className="w-5 h-5 flex-shrink-0" />
          <span>Guidance Withheld — Safety Referral Escalation</span>
        </div>

        <div className="text-xs text-[#9f1239] leading-relaxed space-y-2">
          <p className="font-semibold">{message.withheldReason || "Patient-specific dosing and individual prescription calculations are beyond the governed knowledge scope."}</p>
          <p className="text-[11px]">
            Action Required: Please consult your institution&apos;s clinical pharmacist, attending physician, or access authorized patient monitoring protocols directly.
          </p>
        </div>

        <div className="pt-3 border-t border-[#fecdd3] flex items-center justify-between text-[11px] text-[#9f1239]">
          <span>Human-review escalation triggered</span>
          <span className="font-code text-[10px] bg-[#ffe4e6] px-2 py-0.5 rounded border border-[#fecdd3] font-bold">Referral Active</span>
        </div>
      </SurfaceCard>
    );
  }

  return (
    <SurfaceCard variant="transactional" className="my-4 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[#e5e7eb]">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-[#f7f6fa] border border-[#e5e7eb]">
            <Sparkles className="w-4 h-4 text-[#6a5fc1]" />
          </div>
          <span className="text-xs font-bold text-[#1f1633]">MediTrust AI Assistant</span>
        </div>

        <div className="flex items-center space-x-2">
          {message.badges?.map((badge, idx) => (
            <span
              key={idx}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#f0fdf4] border border-[#bbf7d0] text-[#166534]"
            >
              <ShieldCheck className="w-3 h-3 mr-1 text-[#23865f]" />
              {badge}
            </span>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="text-sm text-[#1f1633] leading-relaxed space-y-3 whitespace-pre-wrap font-sans">
        {message.content}
      </div>

      {/* Cautions */}
      {message.cautions && message.cautions.length > 0 && (
        <CautionPanel cautions={message.cautions} />
      )}

      {/* Citations */}
      {message.citations && message.citations.length > 0 && (
        <CitationList citations={message.citations} onOpenDrawer={onOpenCitationDrawer} />
      )}
    </SurfaceCard>
  );
};
