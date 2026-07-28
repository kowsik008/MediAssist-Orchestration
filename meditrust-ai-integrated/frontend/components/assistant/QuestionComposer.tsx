"use client";

import React from "react";
import { HealthcareRole } from "@/lib/types";
import { ActionButton } from "../shared/ActionButton";
import { Send, Shield, Lock, UserCheck } from "lucide-react";

interface QuestionComposerProps {
  onSubmit: (question: string, role: HealthcareRole) => void;
  isLoading: boolean;
}

export const QuestionComposer: React.FC<QuestionComposerProps> = ({ onSubmit, isLoading }) => {
  const [question, setQuestion] = React.useState("");
  const [selectedRole, setSelectedRole] = React.useState<HealthcareRole>("Nurse");

  const roles: HealthcareRole[] = ["Doctor", "Nurse", "Pharmacist", "Compliance Officer", "Administrator"];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;
    onSubmit(question, selectedRole);
    setQuestion("");
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-3">
      {/* Role & Privacy Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2.5 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-xs">
        <div className="flex items-center space-x-2">
          <UserCheck className="w-4 h-4 text-[#6a5fc1]" />
          <span className="text-[#494256] font-bold">Access Role:</span>
          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value as HealthcareRole)}
            className="bg-white text-[#1f1633] border border-[#cfcbd8] rounded-lg px-2.5 py-1 font-bold focus:outline-none focus:ring-2 focus:ring-[#6a5fc1] shadow-sm"
          >
            {roles.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-1.5 text-[11px] text-[#716a7d]">
          <Lock className="w-3.5 h-3.5 text-[#23865f]" />
          <span>Privacy Reminder: Do not enter patient names or raw PHI.</span>
        </div>
      </div>

      {/* Input Area */}
      <div className="relative rounded-2xl bg-white border border-[#e5e7eb] p-3 shadow-sm focus-within:border-[#6a5fc1] focus-within:ring-2 focus-within:ring-[#6a5fc1]/20 transition-all">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about isolation protocols, clinical guidance, or stewardship..."
          rows={3}
          disabled={isLoading}
          className="w-full bg-transparent text-[#1f1633] placeholder-[#716a7d] text-sm focus:outline-none resize-none font-sans"
        />

        <div className="flex items-center justify-between pt-2 border-t border-[#e5e7eb]">
          <div className="flex items-center space-x-2 text-[11px] text-[#716a7d]">
            <Shield className="w-3.5 h-3.5 text-[#23865f]" />
            <span>Grounded in approved institutional documents</span>
          </div>

          <ActionButton
            type="submit"
            variant="primary"
            size="sm"
            disabled={!question.trim() || isLoading}
          >
            <span>Submit Query</span>
            <Send className="w-3.5 h-3.5" />
          </ActionButton>
        </div>
      </div>
    </form>
  );
};
