"use client";

import React, { useState } from "react";
import { AssistantMessage, Citation, HealthcareRole, PlainProgressStep } from "@/lib/types";
import { QuestionComposer } from "./QuestionComposer";
import { StarterQueryCards } from "./StarterQueryCards";
import { UserProgress } from "./UserProgress";
import { AnswerCard } from "./AnswerCard";
import { EvidenceDrawer } from "./EvidenceDrawer";
import { PageContainer } from "../shell/PageContainer";
import { askAssistant } from "@/lib/api-client";
import { Trash2 } from "lucide-react";

export const AssistantShell: React.FC = () => {
  const [messages, setMessages] = useState<AssistantMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [progressIndex, setProgressIndex] = useState<number>(-1);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const steps: PlainProgressStep[] = [
    "Checking your request",
    "Reviewing safety and scope",
    "Clarifying the search",
    "Searching trusted sources",
    "Reviewing supporting evidence",
    "Preparing a concise summary",
    "Verifying citations and safety",
  ];

  const handleOpenCitation = (cite: Citation) => {
    setSelectedCitation(cite);
    setIsDrawerOpen(true);
  };

  const handleAskQuestion = async (queryText: string, role: HealthcareRole) => {
    const userMsg: AssistantMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      userRole: role,
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setProgressIndex(0);

    const progressTimer = window.setInterval(() => {
      setProgressIndex((current) =>
        current < steps.length - 1 ? current + 1 : current,
      );
    }, 450);

    try {
      const result = await askAssistant(queryText, role);
      const isWithheld = [
        "blocked_by_input_guard",
        "escalated_by_input_guard",
        "blocked_by_output_guard",
        "escalated",
        "insufficient_evidence",
      ].includes(result.final_status);

      const citations: Citation[] = result.citations.map((citation, index) => ({
        id: citation.chunk_id || `cite-${index + 1}`,
        sourceId:
          citation.document_id ||
          citation.chunk_id ||
          result.source_ids[index] ||
          `source-${index + 1}`,
        title: citation.title || "Approved evidence source",
        publisher: citation.publisher || "MediTrust Knowledge Service",
        versionDate: citation.version_date || "Current",
        excerpt: "Retrieved evidence used by the governed orchestration workflow.",
        section: citation.section || "Referenced section",
        isSynthetic: citation.synthetic || citation.is_synthetic || false,
      }));

      const cautions = [...result.warnings, ...result.negative_statements].map(
        (text, index) => ({
          id: `caution-${index + 1}`,
          statementReference: "Governance review",
          text,
          severity: "medium" as const,
        }),
      );

      const assistantMsg: AssistantMessage = {
        id: `ast-${Date.now()}`,
        role: "assistant",
        content: isWithheld ? "" : result.answer,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        isWithheld,
        withheldReason: isWithheld
          ? result.escalation_text || result.answer
          : undefined,
        badges: isWithheld
          ? undefined
          : [
              result.cache_hit ? "Validated cache" : "Evidence reviewed",
              "Governance checked",
            ],
        cautions: isWithheld ? undefined : cautions,
        citations: isWithheld ? undefined : citations,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      const assistantMsg: AssistantMessage = {
        id: `ast-${Date.now()}`,
        role: "assistant",
        content: "",
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        isUnavailable: true,
        withheldReason:
          error instanceof Error
            ? error.message
            : "The governed assistant is temporarily unavailable.",
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } finally {
      window.clearInterval(progressTimer);
      setIsLoading(false);
      setProgressIndex(-1);
    }
  };

  return (
    <PageContainer className="flex flex-col min-h-[calc(100vh-8rem)]">
      {/* Page Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#e5e7eb] mb-4">
        <div>
          <h1 className="text-xl font-bold text-[#1f1633]">Healthcare Knowledge Assistant</h1>
          <p className="text-xs text-[#716a7d]">Plain-language guidance backed by verified citations.</p>
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-white border border-[#e5e7eb] text-xs text-[#716a7d] hover:text-[#1f1633] hover:border-[#cfcbd8] transition-colors shadow-sm cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Thread</span>
          </button>
        )}
      </div>

      {/* Thread */}
      <div className="flex-1 space-y-4 pb-6">
        {messages.length === 0 ? (
          <StarterQueryCards onSelectQuery={(q) => handleAskQuestion(q, "Nurse")} />
        ) : (
          messages.map((msg) => (
            <AnswerCard key={msg.id} message={msg} onOpenCitationDrawer={handleOpenCitation} />
          ))
        )}

        {isLoading && progressIndex >= 0 && (
          <UserProgress currentStepIndex={progressIndex} steps={steps} />
        )}
      </div>

      {/* Sticky Composer */}
      <div className="sticky bottom-4 z-30">
        <QuestionComposer onSubmit={handleAskQuestion} isLoading={isLoading} />
      </div>

      <EvidenceDrawer citation={selectedCitation} isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />
    </PageContainer>
  );
};
