"use client";

import React from "react";
import { Search, Filter } from "lucide-react";

interface EvidenceSearchProps {
  query: string;
  onQueryChange: (q: string) => void;
  onToggleFilters: () => void;
  isFilterOpen: boolean;
}

export const EvidenceSearch: React.FC<EvidenceSearchProps> = ({ query, onQueryChange, onToggleFilters, isFilterOpen }) => {
  return (
    <div className="flex flex-col sm:flex-row items-center gap-3 w-full my-4">
      <div className="relative flex-1 w-full">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search by topic, title, publisher mark, or keyword..."
          className="w-full bg-white border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#1B5FA8] focus:ring-2 focus:ring-blue-100 shadow-sm transition-all"
        />
      </div>

      <button
        onClick={onToggleFilters}
        className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all shadow-sm ${
          isFilterOpen
            ? "bg-blue-50 border-blue-300 text-[#1B5FA8]"
            : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300"
        }`}
      >
        <Filter className="w-3.5 h-3.5" />
        <span>Filter Sources</span>
      </button>
    </div>
  );
};
