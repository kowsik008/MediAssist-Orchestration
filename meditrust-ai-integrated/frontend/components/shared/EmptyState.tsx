"use client";

import React from "react";
import { SurfaceCard } from "./SurfaceCard";
import { ShieldCheck } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  action,
  icon = <ShieldCheck className="w-12 h-12 text-[#23865f] mb-3" />,
}) => {
  return (
    <SurfaceCard variant="transactional" className="flex flex-col items-center justify-center p-10 text-center my-6 border-[#e5e7eb]">
      {icon}
      <h3 className="text-lg font-bold text-[#1f1633] mb-1">{title}</h3>
      <p className="text-sm text-[#716a7d] max-w-md mb-4">{description}</p>
      {action}
    </SurfaceCard>
  );
};
