"use client";

import React, { useEffect, useState } from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { StickerMascot } from "../shared/StickerMascot";
import { fetchStarterQueries, StarterQueryItem } from "@/lib/api-client";
import { Sparkles, ArrowRight } from "lucide-react";

interface StarterQueryCardsProps {
  onSelectQuery: (query: string) => void;
}

export const StarterQueryCards: React.FC<StarterQueryCardsProps> = ({ onSelectQuery }) => {
  const [starters, setStarters] = useState<StarterQueryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStarterQueries().then((data) => {
      setStarters(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-8 px-4 text-center max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Restrained Mascot #3 of 3: Empty State Knowledge Guide */}
      <div className="flex flex-col items-center space-y-3">
        <StickerMascot variant="knowledge-guide" size="lg" title="Knowledge Guide Mascot" />
        <div className="space-y-1">
          <h2 className="text-2xl font-bold text-[#1f1633]">
            How can MediTrust AI assist your team today?
          </h2>
          <p className="text-xs sm:text-sm text-[#716a7d] max-w-lg mx-auto font-normal">
            Enter your inquiry using plain language below.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="text-xs text-[#716a7d] py-4">Loading suggested inquiries...</div>
      ) : starters.length === 0 ? (
        <div className="text-xs text-[#716a7d] py-4">Enter a question to begin a live request.</div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
          {starters.map((item, idx) => (
            <SurfaceCard
              key={idx}
              variant="transactional"
              interactive
              onClick={() => onSelectQuery(item.query)}
              className="p-4 flex flex-col justify-between text-left cursor-pointer border-[#e5e7eb] hover:border-[#6a5fc1]/40 group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] font-code font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${item.tagStyle}`}>
                    {item.category}
                  </span>
                  <Sparkles className="w-3.5 h-3.5 text-[#716a7d] group-hover:text-[#6a5fc1] transition-colors" />
                </div>
                <h3 className="text-sm font-bold text-[#1f1633] mb-1">{item.title}</h3>
                <p className="text-xs text-[#716a7d] line-clamp-2">{item.query}</p>
              </div>

              <div className="pt-3 mt-3 border-t border-[#e5e7eb] flex items-center justify-between text-[11px] text-[#6a5fc1] font-bold">
                <span>Ask this question</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </SurfaceCard>
          ))}
        </div>
      )}
    </div>
  );
};
