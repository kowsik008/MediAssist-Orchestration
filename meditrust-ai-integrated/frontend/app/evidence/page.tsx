"use client";

import React, { useEffect, useState } from "react";
import { PageContainer } from "@/components/shell/PageContainer";
import { EvidenceSearch } from "@/components/evidence/EvidenceSearch";
import { FilterSheet } from "@/components/evidence/FilterSheet";
import { SourceCard } from "@/components/evidence/SourceCard";
import { SourceDetailDrawer } from "@/components/evidence/SourceDetailDrawer";
import { fetchSources } from "@/lib/api-client";
import { EvidenceSource } from "@/lib/types";

export default function EvidencePage() {
  const [sources, setSources] = useState<EvidenceSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState("All");
  const [selectedRole, setSelectedRole] = useState("All");
  const [selectedType, setSelectedType] = useState("All");
  const [activeSource, setActiveSource] = useState<EvidenceSource | null>(null);

  useEffect(() => {
    fetchSources().then((data) => {
      setSources(data);
      setLoading(false);
    });
  }, []);

  const filteredSources = sources.filter((src) => {
    const matchesQuery =
      src.title.toLowerCase().includes(query.toLowerCase()) ||
      src.publisher.toLowerCase().includes(query.toLowerCase()) ||
      src.excerpt.toLowerCase().includes(query.toLowerCase());

    const matchesStatus = selectedStatus === "All" || src.status === selectedStatus;
    const matchesRole = selectedRole === "All" || src.accessRole === selectedRole || src.accessRole === "All Users";
    const matchesType = selectedType === "All" || src.sourceType === selectedType;

    return matchesQuery && matchesStatus && matchesRole && matchesType;
  });

  const handleResetFilters = () => {
    setSelectedStatus("All");
    setSelectedRole("All");
    setSelectedType("All");
    setQuery("");
  };

  return (
    <PageContainer>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Evidence Explorer</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Browse and inspect approved institutional protocols, clinical guidelines, and synthetic benchmarks.
          </p>
        </div>

        <EvidenceSearch
          query={query}
          onQueryChange={setQuery}
          onToggleFilters={() => setIsFilterOpen(!isFilterOpen)}
          isFilterOpen={isFilterOpen}
        />

        <FilterSheet
          isOpen={isFilterOpen}
          selectedStatus={selectedStatus}
          onSelectStatus={setSelectedStatus}
          selectedRole={selectedRole}
          onSelectRole={setSelectedRole}
          selectedType={selectedType}
          onSelectType={setSelectedType}
          onReset={handleResetFilters}
        />

        {loading ? (
          <div className="text-center py-12 text-slate-400 bg-slate-50 border border-slate-200 rounded-2xl">
            Loading evidence documents...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
              {filteredSources.map((source) => (
                <SourceCard key={source.id} source={source} onSelect={setActiveSource} />
              ))}
            </div>

            {filteredSources.length === 0 && (
              <div className="text-center py-12 text-slate-400 bg-slate-50 border border-slate-200 rounded-2xl">
                No source documents found matching your filter criteria.
              </div>
            )}
          </>
        )}
      </div>

      <SourceDetailDrawer
        source={activeSource}
        isOpen={!!activeSource}
        onClose={() => setActiveSource(null)}
      />
    </PageContainer>
  );
}

