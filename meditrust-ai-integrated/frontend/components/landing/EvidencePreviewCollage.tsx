"use client";

import React, { useEffect, useState } from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { StatusBadge } from "../shared/StatusBadge";
import { fetchSources } from "@/lib/api-client";
import { EvidenceSource } from "@/lib/types";
import { FileCheck2, ExternalLink } from "lucide-react";
import Link from "next/link";

export const EvidencePreviewCollage: React.FC = () => {
  const [sources, setSources] = useState<EvidenceSource[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSources().then((data) => {
      setSources(data.slice(0, 3));
      setLoading(false);
    });
  }, []);

  return (
    <section className="py-16 bg-[#ffffff] text-[#1f1633] border-b border-[#e5e7eb]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[#23865f]">Traceable Provenance</span>
            <h2 className="font-display-section text-[#1f1633] mt-1">
              Evidence You Can Inspect
            </h2>
          </div>
          <Link href="/evidence" className="text-xs font-bold text-[#6a5fc1] hover:underline underline-offset-2 flex items-center gap-1">
            <span>Browse all approved documents</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12 text-xs text-[#716a7d]">Loading evidence sources...</div>
        ) : sources.length === 0 ? (
          <div className="text-center py-12 text-xs text-[#716a7d] bg-[#f7f6fa] rounded-2xl border border-[#e5e7eb]">
            No evidence sources currently loaded.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {sources.map((source) => (
              <SurfaceCard
                key={source.id}
                variant="transactional"
                interactive
                className="flex flex-col justify-between p-5 border-[#e5e7eb]"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-code text-[#716a7d] bg-[#f7f6fa] px-2 py-0.5 rounded border border-[#e5e7eb]">
                      {source.version}
                    </span>
                    <StatusBadge
                      status={source.status}
                      variant={source.isSynthetic ? "synthetic" : source.status === "Current" ? "success" : "warning"}
                    />
                  </div>

                  <h3 className="text-base font-bold text-[#1f1633] line-clamp-2 leading-snug">
                    {source.title}
                  </h3>

                  <div className="text-xs text-[#6a5fc1] font-semibold">
                    {source.publisher} <span className="text-[#716a7d] font-normal">• {source.publishDate}</span>
                  </div>

                  <div className="p-3 rounded-xl bg-[#f7f6fa] border border-[#e5e7eb] text-xs text-[#494256] italic line-clamp-3">
                    &ldquo;{source.excerpt}&rdquo;
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-[#e5e7eb] flex items-center justify-between text-[11px] text-[#716a7d]">
                  <div className="flex items-center space-x-1">
                    <FileCheck2 className="w-3.5 h-3.5 text-[#23865f]" />
                    <span>{source.citationCount} active citations</span>
                  </div>
                  <span className="text-[#6a5fc1] font-bold hover:underline cursor-pointer">Inspect excerpt →</span>
                </div>
              </SurfaceCard>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};
