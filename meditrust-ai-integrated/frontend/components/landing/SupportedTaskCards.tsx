"use client";

import React from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { Search, FileCheck, FileText, AlertTriangle, ArrowRight } from "lucide-react";
import Link from "next/link";

export const SupportedTaskCards: React.FC = () => {
  const tasks = [
    {
      title: "Find approved guidance",
      subtitle: "Instant policy retrieval",
      description: "Quickly locate active infection control, isolation protocols, and institutional standards.",
      icon: <Search className="w-5 h-5 text-[#c2ef4e]" />,
      href: "/assistant",
      accentTag: "bg-[#c2ef4e]/15 text-[#c2ef4e] border-[#c2ef4e]/30"
    },
    {
      title: "Review supporting evidence",
      subtitle: "Full provenance metadata",
      description: "Inspect source publishers, version dates, active status, and direct excerpt citations.",
      icon: <FileCheck className="w-5 h-5 text-[#6a5fc1]" />,
      href: "/evidence",
      accentTag: "bg-[#6a5fc1]/20 text-[#6a5fc1] border-[#6a5fc1]/30"
    },
    {
      title: "Summarize complex policies",
      subtitle: "Concise clinical highlights",
      description: "Transform dense multi-page manuals into readable, citation-grounded action points.",
      icon: <FileText className="w-5 h-5 text-[#c2ef4e]" />,
      href: "/assistant",
      accentTag: "bg-[#c2ef4e]/15 text-[#c2ef4e] border-[#c2ef4e]/30"
    },
    {
      title: "Escalate high-risk questions",
      subtitle: "Safety guardrail routing",
      description: "Patient-specific dosing and high-risk treatment decisions automatically trigger referral routes.",
      icon: <AlertTriangle className="w-5 h-5 text-[#fa7faa]" />,
      href: "/assistant",
      accentTag: "bg-[#fa7faa]/20 text-[#fa7faa] border-[#fa7faa]/30"
    }
  ];

  return (
    <section className="py-16 bg-[#1f1633] text-white border-b border-[#362d59]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="font-display-section text-white mb-3">
            Core Supported Tasks
          </h2>
          <p className="text-sm text-[#bbb3c9]">
            Structured workflows designed for speed, accuracy, and clear evidence inspection.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {tasks.map((task, idx) => (
            <SurfaceCard
              key={idx}
              variant="darkFeature"
              interactive
              className="flex flex-col justify-between p-5 group"
            >
              <div className="space-y-4">
                <div className="p-3 rounded-xl bg-[#150f23] border border-[#362d59] w-fit">
                  {task.icon}
                </div>

                <div>
                  <span className={`text-[10px] font-code uppercase tracking-wider px-2 py-0.5 rounded border ${task.accentTag}`}>
                    {task.subtitle}
                  </span>
                  <h3 className="text-base font-bold text-white mt-2 mb-1">{task.title}</h3>
                  <p className="text-xs text-[#bbb3c9] leading-relaxed">{task.description}</p>
                </div>
              </div>

              <div className="pt-4 mt-4 border-t border-[#362d59]">
                <Link
                  href={task.href}
                  className="inline-flex items-center text-xs font-bold text-[#c2ef4e] group-hover:underline underline-offset-2"
                >
                  <span>Explore task</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1 group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </SurfaceCard>
          ))}
        </div>
      </div>
    </section>
  );
};
