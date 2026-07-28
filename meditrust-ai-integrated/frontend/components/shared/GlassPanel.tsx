"use client";

import React from "react";
import { SurfaceCard, SurfaceCardProps } from "./SurfaceCard";

/**
 * @deprecated Use SurfaceCard instead. GlassPanel is retained for backward compatibility.
 */
export const GlassPanel: React.FC<SurfaceCardProps> = (props) => {
  return <SurfaceCard {...props} />;
};
