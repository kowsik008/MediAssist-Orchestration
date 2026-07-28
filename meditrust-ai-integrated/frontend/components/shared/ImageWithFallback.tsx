"use client";

import React, { useState } from "react";
import { cn } from "@/lib/utils";
import { Image as ImageIcon } from "lucide-react";

interface ImageWithFallbackProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  fill?: boolean;
  className?: string;
  priority?: boolean;
}

export const ImageWithFallback: React.FC<ImageWithFallbackProps> = ({
  src,
  alt,
  width,
  height,
  fill = false,
  className,
}) => {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center bg-slate-900 border border-slate-800 text-slate-400 rounded-xl p-4 text-center w-full h-full min-h-[140px]",
          className
        )}
      >
        <ImageIcon className="w-8 h-8 mb-2 text-teal-400/60" />
        <span className="text-xs font-medium text-slate-300">{alt || "Healthcare Guidance Visual"}</span>
      </div>
    );
  }

  return (
    <div className={cn("relative overflow-hidden w-full h-full", className)}>
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        onError={() => setError(true)}
        className={cn("w-full h-full object-cover transition-all duration-300", fill && "absolute inset-0")}
      />
    </div>
  );
};
