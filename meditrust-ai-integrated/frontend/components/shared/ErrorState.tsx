"use client";

import React from "react";
import { SurfaceCard } from "./SurfaceCard";
import { ActionButton } from "./ActionButton";
import { AlertCircle } from "lucide-react";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message = "A temporary operational disruption occurred while querying guidance.",
  onRetry,
}) => {
  return (
    <SurfaceCard variant="rose" className="p-6 flex flex-col items-center text-center">
      <AlertCircle className="w-10 h-10 text-[#b5414c] mb-2" />
      <h4 className="text-base font-bold text-[#9f1239] mb-1">Notice</h4>
      <p className="text-sm text-[#9f1239] max-w-md mb-4">{message}</p>
      {onRetry && (
        <ActionButton variant="danger" size="sm" onClick={onRetry}>
          Try Again
        </ActionButton>
      )}
    </SurfaceCard>
  );
};
