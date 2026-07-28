"use client";

import React from "react";
import { ImageWithFallback } from "../shared/ImageWithFallback";

interface SourceThumbnailProps {
  src: string;
  alt: string;
}

export const SourceThumbnail: React.FC<SourceThumbnailProps> = ({ src, alt }) => {
  return (
    <div className="relative aspect-[4/3] w-full rounded-xl overflow-hidden bg-slate-900 border border-white/10">
      <ImageWithFallback src={src} alt={alt} fill className="object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent pointer-events-none" />
    </div>
  );
};
